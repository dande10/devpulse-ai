import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_notification_email(subject: str, body: str) -> None:
    """Best-effort email notification for feedback and technology requests.

    Silently (well, loudly in the logs) does nothing until SMTP_HOST,
    SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, and NOTIFY_EMAIL are all set —
    this lets the feature ship now and start delivering real email the
    moment those are configured, with no further code changes.
    """
    if not (settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.smtp_from_email and settings.notify_email):
        # .info() is silently dropped under this app's default logging config
        # (root logger defaults to WARNING) — .warning() so this is actually
        # visible without needing a separate logging setup.
        logger.warning("Email notification skipped (SMTP not configured): %s", subject)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = settings.notify_email
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as client:
            client.starttls()
            client.login(settings.smtp_user, settings.smtp_password)
            client.send_message(message)
    except Exception:
        logger.exception("Failed to send email notification: %s", subject)
