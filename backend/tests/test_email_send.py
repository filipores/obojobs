"""Tests for email send endpoint (POST /api/email/send)."""

from unittest.mock import patch

from models import Application, EmailAccount, db


class TestSendEmailValidation:
    """Validation tests for POST /api/email/send"""

    def test_requires_auth(self, client):
        response = client.post("/api/email/send", json={})
        assert response.status_code == 401

    def test_missing_application_id(self, client, auth_headers):
        response = client.post(
            "/api/email/send",
            json={"email_account_id": 1, "subject": "T", "body": "T", "to_email": "a@b.com"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_email_account_id(self, client, auth_headers):
        response = client.post(
            "/api/email/send",
            json={"application_id": 1, "subject": "T", "body": "T", "to_email": "a@b.com"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_subject(self, client, auth_headers):
        response = client.post(
            "/api/email/send",
            json={"application_id": 1, "email_account_id": 1, "body": "T", "to_email": "a@b.com"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_body(self, client, auth_headers):
        response = client.post(
            "/api/email/send",
            json={"application_id": 1, "email_account_id": 1, "subject": "T", "to_email": "a@b.com"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_to_email(self, client, auth_headers):
        response = client.post(
            "/api/email/send",
            json={"application_id": 1, "email_account_id": 1, "subject": "T", "body": "T"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_application_not_found(self, client, auth_headers):
        response = client.post(
            "/api/email/send",
            json={"application_id": 9999, "email_account_id": 1, "subject": "T", "body": "T", "to_email": "a@b.com"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_email_account_not_found(self, app, client, test_user, auth_headers):
        with app.app_context():
            a = Application(user_id=test_user["id"], firma="Test", status="erstellt")
            db.session.add(a)
            db.session.commit()
            aid = a.id

        response = client.post(
            "/api/email/send",
            json={"application_id": aid, "email_account_id": 9999, "subject": "T", "body": "T", "to_email": "a@b.com"},
            headers=auth_headers,
        )
        assert response.status_code == 404


def _setup_app_and_account(app, test_user, provider="gmail"):
    """Helper to create application and email account."""
    with app.app_context():
        application = Application(user_id=test_user["id"], firma="Test", status="erstellt")
        db.session.add(application)
        account = EmailAccount(user_id=test_user["id"], provider=provider, email=f"u@{provider}.com")
        db.session.add(account)
        db.session.commit()
        return application.id, account.id


class TestSendEmailProviders:
    """Provider-specific tests for POST /api/email/send"""

    @patch("routes.email.send.GmailService.send_email")
    def test_send_gmail_success(self, mock_send, app, client, test_user, auth_headers):
        mock_send.return_value = {"message_id": "msg-123"}
        aid, eid = _setup_app_and_account(app, test_user, "gmail")

        response = client.post(
            "/api/email/send",
            json={
                "application_id": aid,
                "email_account_id": eid,
                "subject": "B",
                "body": "Text",
                "to_email": "hr@co.com",
                "attachments": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["provider"] == "gmail"

    @patch("routes.email.send.OutlookService.send_email")
    def test_send_outlook_success(self, mock_send, app, client, test_user, auth_headers):
        mock_send.return_value = {"message_id": "msg-456"}
        aid, eid = _setup_app_and_account(app, test_user, "outlook")

        response = client.post(
            "/api/email/send",
            json={
                "application_id": aid,
                "email_account_id": eid,
                "subject": "B",
                "body": "Text",
                "to_email": "hr@co.com",
                "attachments": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["provider"] == "outlook"

    def test_unknown_provider(self, app, client, test_user, auth_headers):
        aid, eid = _setup_app_and_account(app, test_user, "yahoo")

        response = client.post(
            "/api/email/send",
            json={
                "application_id": aid,
                "email_account_id": eid,
                "subject": "T",
                "body": "T",
                "to_email": "hr@co.com",
                "attachments": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.email.send.GmailService.send_email")
    def test_send_value_error(self, mock_send, app, client, test_user, auth_headers):
        mock_send.side_effect = ValueError("Token expired")
        aid, eid = _setup_app_and_account(app, test_user, "gmail")

        response = client.post(
            "/api/email/send",
            json={
                "application_id": aid,
                "email_account_id": eid,
                "subject": "T",
                "body": "T",
                "to_email": "hr@co.com",
                "attachments": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.email.send.GmailService.send_email")
    def test_send_generic_error(self, mock_send, app, client, test_user, auth_headers):
        mock_send.side_effect = RuntimeError("Network error")
        aid, eid = _setup_app_and_account(app, test_user, "gmail")

        response = client.post(
            "/api/email/send",
            json={
                "application_id": aid,
                "email_account_id": eid,
                "subject": "T",
                "body": "T",
                "to_email": "hr@co.com",
                "attachments": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 500
