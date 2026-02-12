"""Tests for email routes - accounts, OAuth flows (routes/email.py)."""

import os
from unittest.mock import MagicMock, patch

from models import EmailAccount, db


class TestIntegrationStatus:
    """Tests for GET /api/email/integration-status"""

    def test_requires_auth(self, client):
        response = client.get("/api/email/integration-status")
        assert response.status_code == 401

    @patch.dict(os.environ, {}, clear=True)
    def test_both_unconfigured(self, client, auth_headers):
        for key in [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
            "MICROSOFT_CLIENT_ID",
            "MICROSOFT_CLIENT_SECRET",
            "MICROSOFT_REDIRECT_URI",
        ]:
            os.environ.pop(key, None)

        response = client.get("/api/email/integration-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["gmail"]["configured"] is False
        assert data["data"]["outlook"]["configured"] is False

    def test_gmail_configured(self, client, auth_headers):
        env = {"GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "s", "GOOGLE_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            response = client.get("/api/email/integration-status", headers=auth_headers)
            assert response.get_json()["data"]["gmail"]["configured"] is True


class TestListEmailAccounts:
    """Tests for GET /api/email/accounts"""

    def test_requires_auth(self, client):
        assert client.get("/api/email/accounts").status_code == 401

    def test_empty_list(self, client, auth_headers):
        response = client.get("/api/email/accounts", headers=auth_headers)
        assert response.get_json()["data"] == []

    def test_returns_accounts(self, app, client, test_user, auth_headers):
        with app.app_context():
            db.session.add(EmailAccount(user_id=test_user["id"], provider="gmail", email="u@g.com"))
            db.session.commit()
        assert len(client.get("/api/email/accounts", headers=auth_headers).get_json()["data"]) == 1


class TestDeleteEmailAccount:
    """Tests for DELETE /api/email/accounts/<id>"""

    def test_requires_auth(self, client):
        assert client.delete("/api/email/accounts/1").status_code == 401

    def test_delete_success(self, app, client, test_user, auth_headers):
        with app.app_context():
            a = EmailAccount(user_id=test_user["id"], provider="gmail", email="u@g.com")
            db.session.add(a)
            db.session.commit()
            aid = a.id
        assert client.delete(f"/api/email/accounts/{aid}", headers=auth_headers).status_code == 200

    def test_delete_not_found(self, client, auth_headers):
        assert client.delete("/api/email/accounts/9999", headers=auth_headers).status_code == 404


class TestGmailAuthUrl:
    """Tests for GET /api/email/gmail/auth-url"""

    def test_requires_auth(self, client):
        assert client.get("/api/email/gmail/auth-url").status_code == 401

    def test_not_configured(self, client, auth_headers):
        for k in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]:
            os.environ.pop(k, None)
        assert client.get("/api/email/gmail/auth-url", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.GmailService.get_authorization_url")
    def test_success(self, mock_url, client, auth_headers):
        mock_url.return_value = ("https://accounts.google.com/auth", "s")
        env = {"GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "s", "GOOGLE_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            r = client.get("/api/email/gmail/auth-url", headers=auth_headers)
            assert r.status_code == 200 and "authorization_url" in r.get_json()

    @patch("routes.email.oauth.GmailService.get_authorization_url")
    def test_value_error(self, mock_url, client, auth_headers):
        mock_url.side_effect = ValueError("Missing")
        env = {"GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "s", "GOOGLE_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            assert client.get("/api/email/gmail/auth-url", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.GmailService.get_authorization_url")
    def test_generic_error(self, mock_url, client, auth_headers):
        mock_url.side_effect = RuntimeError("boom")
        env = {"GOOGLE_CLIENT_ID": "id", "GOOGLE_CLIENT_SECRET": "s", "GOOGLE_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            assert client.get("/api/email/gmail/auth-url", headers=auth_headers).status_code == 500


class TestGmailCallback:
    """Tests for GET /api/email/gmail/callback"""

    def test_requires_auth(self, client):
        assert client.get("/api/email/gmail/callback?code=t").status_code == 401

    def test_oauth_error(self, client, auth_headers):
        r = client.get("/api/email/gmail/callback?error=access_denied", headers=auth_headers)
        assert r.status_code == 400

    def test_missing_code(self, client, auth_headers):
        assert client.get("/api/email/gmail/callback", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.GmailService.save_tokens")
    @patch("routes.email.oauth.GmailService.get_user_email")
    @patch("routes.email.oauth.GmailService.exchange_code_for_tokens")
    def test_success(self, mock_ex, mock_email, mock_save, client, auth_headers):
        mock_ex.return_value = {"access_token": "a", "refresh_token": "r"}
        mock_email.return_value = "u@g.com"
        m = MagicMock()
        m.to_dict.return_value = {"id": 1, "email": "u@g.com", "provider": "gmail"}
        mock_save.return_value = m
        assert client.get("/api/email/gmail/callback?code=c", headers=auth_headers).status_code == 200

    @patch("routes.email.oauth.GmailService.exchange_code_for_tokens")
    def test_value_error(self, mock_ex, client, auth_headers):
        mock_ex.side_effect = ValueError("bad")
        assert client.get("/api/email/gmail/callback?code=c", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.GmailService.exchange_code_for_tokens")
    def test_generic_error(self, mock_ex, client, auth_headers):
        mock_ex.side_effect = RuntimeError("net")
        assert client.get("/api/email/gmail/callback?code=c", headers=auth_headers).status_code == 500


class TestOutlookAuthUrl:
    """Tests for GET /api/email/outlook/auth-url"""

    def test_requires_auth(self, client):
        assert client.get("/api/email/outlook/auth-url").status_code == 401

    def test_not_configured(self, client, auth_headers):
        for k in ["MICROSOFT_CLIENT_ID", "MICROSOFT_CLIENT_SECRET", "MICROSOFT_REDIRECT_URI"]:
            os.environ.pop(k, None)
        assert client.get("/api/email/outlook/auth-url", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.OutlookService.get_authorization_url")
    def test_success(self, mock_url, client, auth_headers):
        mock_url.return_value = ("https://login.microsoft.com/auth", "s")
        env = {"MICROSOFT_CLIENT_ID": "id", "MICROSOFT_CLIENT_SECRET": "s", "MICROSOFT_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            assert client.get("/api/email/outlook/auth-url", headers=auth_headers).status_code == 200

    @patch("routes.email.oauth.OutlookService.get_authorization_url")
    def test_value_error(self, mock_url, client, auth_headers):
        mock_url.side_effect = ValueError("Missing")
        env = {"MICROSOFT_CLIENT_ID": "id", "MICROSOFT_CLIENT_SECRET": "s", "MICROSOFT_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            assert client.get("/api/email/outlook/auth-url", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.OutlookService.get_authorization_url")
    def test_generic_error(self, mock_url, client, auth_headers):
        mock_url.side_effect = RuntimeError("boom")
        env = {"MICROSOFT_CLIENT_ID": "id", "MICROSOFT_CLIENT_SECRET": "s", "MICROSOFT_REDIRECT_URI": "http://x"}
        with patch.dict(os.environ, env):
            assert client.get("/api/email/outlook/auth-url", headers=auth_headers).status_code == 500


class TestOutlookCallback:
    """Tests for GET /api/email/outlook/callback"""

    def test_requires_auth(self, client):
        assert client.get("/api/email/outlook/callback?code=t").status_code == 401

    def test_oauth_error(self, client, auth_headers):
        assert client.get("/api/email/outlook/callback?error=denied", headers=auth_headers).status_code == 400

    def test_missing_code(self, client, auth_headers):
        assert client.get("/api/email/outlook/callback", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.OutlookService.save_tokens")
    @patch("routes.email.oauth.OutlookService.get_user_email")
    @patch("routes.email.oauth.OutlookService.exchange_code_for_tokens")
    def test_success(self, mock_ex, mock_email, mock_save, client, auth_headers):
        mock_ex.return_value = {"access_token": "a", "refresh_token": "r"}
        mock_email.return_value = "u@o.com"
        m = MagicMock()
        m.to_dict.return_value = {"id": 1, "email": "u@o.com", "provider": "outlook"}
        mock_save.return_value = m
        assert client.get("/api/email/outlook/callback?code=c", headers=auth_headers).status_code == 200

    @patch("routes.email.oauth.OutlookService.exchange_code_for_tokens")
    def test_value_error(self, mock_ex, client, auth_headers):
        mock_ex.side_effect = ValueError("bad")
        assert client.get("/api/email/outlook/callback?code=c", headers=auth_headers).status_code == 400

    @patch("routes.email.oauth.OutlookService.exchange_code_for_tokens")
    def test_generic_error(self, mock_ex, client, auth_headers):
        mock_ex.side_effect = RuntimeError("net")
        assert client.get("/api/email/outlook/callback?code=c", headers=auth_headers).status_code == 500
