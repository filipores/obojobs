"""
Email Service for transactional emails.

Sends verification and password reset emails via SMTP (Gmail).
Falls back to console logging if SMTP is not configured.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import config

logger = logging.getLogger(__name__)

# Frontend base URL for links in emails
FRONTEND_URL = config.CORS_ORIGINS[0] if config.CORS_ORIGINS else "http://localhost:3000"


def _is_configured() -> bool:
    """Check if email sending is configured."""
    return bool(config.MAIL_USERNAME and config.MAIL_PASSWORD)


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP."""
    if not _is_configured():
        logger.warning("Email not configured - logging instead of sending")
        logger.info(f"Would send to {to_email}: {subject}")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = config.MAIL_DEFAULT_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(config.MAIL_SERVER, config.MAIL_PORT, timeout=10)
        server.starttls()
        server.login(config.MAIL_USERNAME, config.MAIL_PASSWORD)
        server.sendmail(config.MAIL_DEFAULT_SENDER, to_email, msg.as_string())
        server.quit()
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, token: str) -> bool:
    """Send email verification link."""
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    subject = "obo – E-Mail-Adresse bestätigen"

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 20px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 24px; font-weight: 600; color: #1a1a1a; margin: 0;">obo</h1>
      </div>

      <h2 style="font-size: 20px; font-weight: 600; color: #1a1a1a; margin: 0 0 16px;">
        E-Mail bestätigen
      </h2>

      <p style="font-size: 15px; color: #4a4a4a; line-height: 1.6; margin: 0 0 24px;">
        Klicken Sie auf den Button, um Ihre E-Mail-Adresse zu bestätigen und Ihr Konto zu aktivieren.
      </p>

      <div style="text-align: center; margin: 32px 0;">
        <a href="{verify_url}"
           style="display: inline-block; background: #1a1a1a; color: #ffffff; text-decoration: none;
                  padding: 12px 32px; border-radius: 6px; font-size: 15px; font-weight: 500;">
          E-Mail bestätigen
        </a>
      </div>

      <p style="font-size: 13px; color: #888; line-height: 1.5; margin: 24px 0 0;">
        Falls der Button nicht funktioniert, kopieren Sie diesen Link:<br>
        <a href="{verify_url}" style="color: #666; word-break: break-all;">{verify_url}</a>
      </p>

      <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0 16px;">
      <p style="font-size: 12px; color: #aaa; margin: 0;">
        Diese E-Mail wurde automatisch versendet. Falls Sie sich nicht registriert haben, ignorieren Sie diese Nachricht.
      </p>
    </div>
    """

    return _send_email(to_email, subject, html)


def send_password_reset_email(to_email: str, token: str) -> bool:
    """Send password reset link."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = "obo – Passwort zurücksetzen"

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 520px; margin: 0 auto; padding: 32px 20px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 24px; font-weight: 600; color: #1a1a1a; margin: 0;">obo</h1>
      </div>

      <h2 style="font-size: 20px; font-weight: 600; color: #1a1a1a; margin: 0 0 16px;">
        Passwort zurücksetzen
      </h2>

      <p style="font-size: 15px; color: #4a4a4a; line-height: 1.6; margin: 0 0 24px;">
        Sie haben eine Anfrage zum Zurücksetzen Ihres Passworts gestellt.
        Klicken Sie auf den Button, um ein neues Passwort zu wählen.
      </p>

      <div style="text-align: center; margin: 32px 0;">
        <a href="{reset_url}"
           style="display: inline-block; background: #1a1a1a; color: #ffffff; text-decoration: none;
                  padding: 12px 32px; border-radius: 6px; font-size: 15px; font-weight: 500;">
          Neues Passwort wählen
        </a>
      </div>

      <p style="font-size: 13px; color: #888; line-height: 1.5; margin: 24px 0 0;">
        Der Link ist <strong>1 Stunde</strong> gültig.<br>
        Falls der Button nicht funktioniert:<br>
        <a href="{reset_url}" style="color: #666; word-break: break-all;">{reset_url}</a>
      </p>

      <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0 16px;">
      <p style="font-size: 12px; color: #aaa; margin: 0;">
        Falls Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail. Ihr Passwort bleibt unverändert.
      </p>
    </div>
    """

    return _send_email(to_email, subject, html)
