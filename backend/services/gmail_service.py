import os
from datetime import datetime, timedelta

from google_auth_oauthlib.flow import Flow

from models import EmailAccount, db

# Gmail OAuth scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


class GmailService:
    """Service for Gmail OAuth 2.0 authentication and token management."""

    @staticmethod
    def get_client_config():
        """Get Google OAuth client configuration from environment variables."""
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

        if not client_id or not client_secret:
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set"
            )

        if not redirect_uri:
            raise ValueError("GOOGLE_REDIRECT_URI must be set")

        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        }

    @staticmethod
    def get_authorization_url(state=None):
        """
        Generate the Google OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            tuple: (authorization_url, state)
        """
        client_config = GmailService.get_client_config()
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

        flow = Flow.from_client_config(
            client_config,
            scopes=GMAIL_SCOPES,
            redirect_uri=redirect_uri,
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        return authorization_url, state

    @staticmethod
    def exchange_code_for_tokens(code):
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            dict: Token information including access_token, refresh_token, expires_at
        """
        client_config = GmailService.get_client_config()
        redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")

        flow = Flow.from_client_config(
            client_config,
            scopes=GMAIL_SCOPES,
            redirect_uri=redirect_uri,
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Calculate token expiration
        expires_at = None
        if credentials.expiry:
            expires_at = credentials.expiry

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_at": expires_at,
        }

    @staticmethod
    def get_user_email(access_token):
        """
        Get the user's email address using the access token.

        Args:
            access_token: Valid Google access token

        Returns:
            str: User's email address
        """
        import requests

        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        user_info = response.json()
        return user_info.get("email")

    @staticmethod
    def refresh_access_token(email_account):
        """
        Refresh the access token for an email account.

        Args:
            email_account: EmailAccount model instance

        Returns:
            str: New access token
        """
        import requests

        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        refresh_token = email_account.get_refresh_token()
        if not refresh_token:
            raise ValueError("No refresh token available")

        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        response.raise_for_status()
        token_data = response.json()

        # Update the email account with new token
        email_account.set_access_token(token_data["access_token"])
        email_account.token_expires_at = datetime.utcnow() + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )
        db.session.commit()

        return token_data["access_token"]

    @staticmethod
    def get_valid_access_token(email_account):
        """
        Get a valid access token, refreshing if necessary.

        Args:
            email_account: EmailAccount model instance

        Returns:
            str: Valid access token
        """
        if email_account.is_token_expired():
            return GmailService.refresh_access_token(email_account)
        return email_account.get_access_token()

    @staticmethod
    def save_tokens(user_id, email, token_data):
        """
        Save or update OAuth tokens for a user.

        Args:
            user_id: User ID
            email: Gmail address
            token_data: Dict with access_token, refresh_token, expires_at

        Returns:
            EmailAccount: The created or updated email account
        """
        # Check if account already exists
        existing = EmailAccount.query.filter_by(
            user_id=user_id,
            provider="gmail",
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
            provider="gmail",
            email=email,
        )
        account.set_access_token(token_data["access_token"])
        if token_data.get("refresh_token"):
            account.set_refresh_token(token_data["refresh_token"])
        account.token_expires_at = token_data.get("expires_at")

        db.session.add(account)
        db.session.commit()

        return account
