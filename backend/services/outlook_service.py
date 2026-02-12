import base64
import os
from datetime import datetime, timedelta
from typing import Any

import msal
import requests

from models import EmailAccount, db

# Outlook/Microsoft Graph OAuth scopes
OUTLOOK_SCOPES = [
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/User.Read",
]


class OutlookService:
    """Service for Microsoft/Outlook OAuth 2.0 authentication and token management."""

    @staticmethod
    def get_client_config() -> dict[str, str]:
        """Get Microsoft OAuth client configuration from environment variables."""
        client_id = os.environ.get("MICROSOFT_CLIENT_ID")
        client_secret = os.environ.get("MICROSOFT_CLIENT_SECRET")
        redirect_uri = os.environ.get("MICROSOFT_REDIRECT_URI")

        if not client_id or not client_secret:
            raise ValueError("MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET must be set")

        if not redirect_uri:
            raise ValueError("MICROSOFT_REDIRECT_URI must be set")

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "authority": "https://login.microsoftonline.com/common",
        }

    @staticmethod
    def get_msal_app() -> msal.ConfidentialClientApplication:
        """Create an MSAL ConfidentialClientApplication instance."""
        config = OutlookService.get_client_config()
        return msal.ConfidentialClientApplication(
            config["client_id"],
            authority=config["authority"],
            client_credential=config["client_secret"],
        )

    @staticmethod
    def get_authorization_url(state: str | None = None) -> tuple[str, str | None]:
        """
        Generate the Microsoft OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            tuple: (authorization_url, state)
        """
        config = OutlookService.get_client_config()
        app = OutlookService.get_msal_app()

        auth_url = app.get_authorization_request_url(
            scopes=OUTLOOK_SCOPES,
            state=state,
            redirect_uri=config["redirect_uri"],
        )

        return auth_url, state

    @staticmethod
    def exchange_code_for_tokens(code: str) -> dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            dict: Token information including access_token, refresh_token, expires_at
        """
        config = OutlookService.get_client_config()
        app = OutlookService.get_msal_app()

        result = app.acquire_token_by_authorization_code(
            code,
            scopes=OUTLOOK_SCOPES,
            redirect_uri=config["redirect_uri"],
        )

        if "error" in result:
            error_desc = result.get("error_description", result.get("error"))
            raise ValueError(f"Token exchange failed: {error_desc}")

        # Calculate token expiration
        expires_in = result.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "expires_at": expires_at,
        }

    @staticmethod
    def get_user_email(access_token: str) -> str | None:
        """
        Get the user's email address using the access token.

        Args:
            access_token: Valid Microsoft access token

        Returns:
            str: User's email address
        """
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        user_info = response.json()
        # Microsoft Graph returns mail or userPrincipalName
        return user_info.get("mail") or user_info.get("userPrincipalName")

    @staticmethod
    def refresh_access_token(email_account: EmailAccount) -> str:
        """
        Refresh the access token for an email account.

        Args:
            email_account: EmailAccount model instance

        Returns:
            str: New access token
        """
        refresh_token = email_account.get_refresh_token()
        if not refresh_token:
            raise ValueError("No refresh token available")

        app = OutlookService.get_msal_app()

        # MSAL handles token refresh via acquire_token_by_refresh_token
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=OUTLOOK_SCOPES,
        )

        if "error" in result:
            error_desc = result.get("error_description", result.get("error"))
            raise ValueError(f"Token refresh failed: {error_desc}")

        # Update the email account with new token
        email_account.set_access_token(result["access_token"])
        if result.get("refresh_token"):
            email_account.set_refresh_token(result["refresh_token"])
        expires_in = result.get("expires_in", 3600)
        email_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        db.session.commit()

        return result["access_token"]

    @staticmethod
    def get_valid_access_token(email_account: EmailAccount) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Args:
            email_account: EmailAccount model instance

        Returns:
            str: Valid access token
        """
        if email_account.is_token_expired():
            return OutlookService.refresh_access_token(email_account)
        return email_account.get_access_token()

    @staticmethod
    def save_tokens(user_id: int, email: str, token_data: dict[str, Any]) -> EmailAccount:
        """
        Save or update OAuth tokens for a user.

        Args:
            user_id: User ID
            email: Outlook email address
            token_data: Dict with access_token, refresh_token, expires_at

        Returns:
            EmailAccount: The created or updated email account
        """
        # Check if account already exists
        existing = EmailAccount.query.filter_by(
            user_id=user_id,
            provider="outlook",
            email=email,
        ).first()

        if existing:
            # Update existing account
            existing.set_access_token(token_data["access_token"])
            if token_data.get("refresh_token"):
                existing.set_refresh_token(token_data["refresh_token"])
            existing.token_expires_at = token_data.get("expires_at")
            db.session.commit()
            return existing

        # Create new account
        account = EmailAccount(
            user_id=user_id,
            provider="outlook",
            email=email,
        )
        account.set_access_token(token_data["access_token"])
        if token_data.get("refresh_token"):
            account.set_refresh_token(token_data["refresh_token"])
        account.token_expires_at = token_data.get("expires_at")

        db.session.add(account)
        db.session.commit()

        return account

    @staticmethod
    def send_email(
        email_account: EmailAccount,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[dict[str, str]] | None = None,
    ) -> dict[str, str | int]:
        """
        Send an email via Microsoft Graph API.

        Args:
            email_account: EmailAccount model instance
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            attachments: List of dicts with 'path' and 'filename' keys

        Returns:
            dict: Response from Graph API

        Raises:
            ValueError: If sending fails
        """
        access_token = OutlookService.get_valid_access_token(email_account)

        # Build the message payload
        message_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": body,
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email,
                        }
                    }
                ],
            },
            "saveToSentItems": "true",
        }

        # Add attachments if provided
        if attachments:
            attachment_list = []
            for attachment in attachments:
                file_path = attachment.get("path")
                filename = attachment.get("filename")

                if not os.path.exists(file_path):
                    raise ValueError(f"Attachment file not found: {file_path}")

                with open(file_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode()

                attachment_list.append(
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentBytes": content,
                    }
                )

            message_payload["message"]["attachments"] = attachment_list

        # Send via Microsoft Graph API
        response = requests.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=message_payload,
            timeout=30,
        )

        if response.status_code not in (200, 202):
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            raise ValueError(f"Failed to send email: {error_msg}")

        return {"status": "sent", "code": response.status_code}
