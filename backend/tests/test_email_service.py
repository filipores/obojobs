"""Tests for email service (services/email_service.py)."""

from unittest.mock import MagicMock, patch

from services.email_service import (
    _is_configured,
    _send_email,
    send_password_reset_email,
    send_verification_email,
)


class TestEmailServiceConfig:
    """Tests for email configuration detection."""

    @patch("services.email_service.config")
    def test_configured_with_credentials(self, mock_config):
        mock_config.MAIL_USERNAME = "user@gmail.com"
        mock_config.MAIL_PASSWORD = "app-password"
        assert _is_configured() is True

    @patch("services.email_service.config")
    def test_not_configured_without_username(self, mock_config):
        mock_config.MAIL_USERNAME = ""
        mock_config.MAIL_PASSWORD = "pass"
        assert _is_configured() is False

    @patch("services.email_service.config")
    def test_not_configured_without_password(self, mock_config):
        mock_config.MAIL_USERNAME = "user"
        mock_config.MAIL_PASSWORD = ""
        assert _is_configured() is False


class TestSendEmail:
    """Tests for _send_email function."""

    @patch("services.email_service.config")
    def test_logs_when_not_configured(self, mock_config):
        mock_config.MAIL_USERNAME = ""
        mock_config.MAIL_PASSWORD = ""

        result = _send_email("to@test.com", "Subject", "<p>Body</p>")
        assert result is False

    @patch("services.email_service.smtplib.SMTP")
    @patch("services.email_service.config")
    def test_sends_email_successfully(self, mock_config, mock_smtp_cls):
        mock_config.MAIL_USERNAME = "user@gmail.com"
        mock_config.MAIL_PASSWORD = "password"
        mock_config.MAIL_SERVER = "smtp.gmail.com"
        mock_config.MAIL_PORT = 587
        mock_config.MAIL_DEFAULT_SENDER = "noreply@obo.de"

        mock_server = MagicMock()
        mock_smtp_cls.return_value = mock_server

        result = _send_email("to@test.com", "Subject", "<p>Body</p>")
        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@gmail.com", "password")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("services.email_service.smtplib.SMTP")
    @patch("services.email_service.config")
    def test_handles_smtp_error(self, mock_config, mock_smtp_cls):
        mock_config.MAIL_USERNAME = "user@gmail.com"
        mock_config.MAIL_PASSWORD = "password"
        mock_config.MAIL_SERVER = "smtp.gmail.com"
        mock_config.MAIL_PORT = 587
        mock_config.MAIL_DEFAULT_SENDER = "noreply@obo.de"

        mock_smtp_cls.side_effect = ConnectionError("SMTP connection failed")

        result = _send_email("to@test.com", "Subject", "<p>Body</p>")
        assert result is False


class TestSendVerificationEmail:
    """Tests for send_verification_email."""

    @patch("services.email_service._send_email")
    def test_sends_with_correct_params(self, mock_send):
        mock_send.return_value = True

        result = send_verification_email("user@test.com", "token-123")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert args[0][0] == "user@test.com"
        assert "bestätigen" in args[0][1]
        assert "token-123" in args[0][2]


class TestSendPasswordResetEmail:
    """Tests for send_password_reset_email."""

    @patch("services.email_service._send_email")
    def test_sends_with_correct_params(self, mock_send):
        mock_send.return_value = True

        result = send_password_reset_email("user@test.com", "reset-token")
        assert result is True
        mock_send.assert_called_once()
        args = mock_send.call_args
        assert args[0][0] == "user@test.com"
        assert "zurücksetzen" in args[0][1]
        assert "reset-token" in args[0][2]
