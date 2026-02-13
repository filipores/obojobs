"""Service layer for email route data access."""

from datetime import datetime

from models import db
from models.application import Application
from models.document import Document
from models.email_account import EmailAccount


def get_email_accounts(user_id: int) -> list[EmailAccount]:
    """Return all email accounts for a user."""
    return EmailAccount.query.filter_by(user_id=user_id).all()


def get_email_account(account_id: int, user_id: int) -> EmailAccount | None:
    """Return a single email account owned by user, or None."""
    return EmailAccount.query.filter_by(id=account_id, user_id=user_id).first()


def delete_email_account(account: EmailAccount) -> None:
    """Delete an email account record."""
    db.session.delete(account)
    db.session.commit()


def get_application(application_id: int, user_id: int) -> Application | None:
    """Return a single application owned by user, or None."""
    return Application.query.filter_by(id=application_id, user_id=user_id).first()


def get_cv_document(user_id: int) -> Document | None:
    """Return the most recent CV PDF document for a user, or None."""
    return (
        Document.query.filter_by(
            user_id=user_id,
            doc_type="cv_pdf",
        )
        .order_by(Document.uploaded_at.desc())
        .first()
    )


def mark_application_sent(application: Application, provider: str) -> None:
    """Mark an application as sent via the given provider."""
    application.sent_at = datetime.utcnow()
    application.sent_via = provider
    application.status = "versendet"
    db.session.commit()
