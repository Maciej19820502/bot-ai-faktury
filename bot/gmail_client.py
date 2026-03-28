"""Gmail integration via IMAP/SMTP with App Password."""

import os
import imaplib
import smtplib
import email
import email.utils
import logging
from email.mime.text import MIMEText
from email.header import decode_header

from bot.config import load_config

logger = logging.getLogger(__name__)

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _get_credentials() -> tuple[str, str]:
    """Get Gmail credentials from config.json, falling back to env vars."""
    config = load_config()
    user = config.get("gmail_user", "") or os.environ.get("GMAIL_USER", "")
    password = config.get("gmail_app_password", "") or os.environ.get("GMAIL_APP_PASSWORD", "")
    return user, password


def _check_credentials():
    user, password = _get_credentials()
    if not user or not password:
        raise ValueError(
            "Brak danych logowania Gmail.\n"
            "Wpisz je w panelu (Konfiguracja) lub w pliku .env"
        )


def _decode_header_value(value):
    """Decode email header (handles encoded subjects etc.)."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_body(msg) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def authenticate():
    """Return None — kept for compatibility. Credentials checked on use."""
    _check_credentials()
    return None


def get_unread_messages(service=None, max_results: int = 10) -> list[dict]:
    """Fetch unread emails from inbox via IMAP."""
    _check_credentials()

    user, password = _get_credentials()
    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(user, password)
    imap.select("INBOX")

    status, data = imap.search(None, "UNSEEN")
    if status != "OK" or not data[0]:
        imap.logout()
        return []

    msg_ids = data[0].split()
    # Take only the latest max_results
    msg_ids = msg_ids[-max_results:]

    parsed = []
    for msg_id in msg_ids:
        status, msg_data = imap.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        from_header = _decode_header_value(msg.get("From", ""))
        subject = _decode_header_value(msg.get("Subject", ""))
        date = msg.get("Date", "")
        message_id = msg.get("Message-ID", "")
        body = _extract_body(msg)

        parsed.append({
            "id": msg_id.decode(),  # IMAP sequence number
            "message_id": message_id,
            "thread_id": message_id,  # Use Message-ID as thread reference
            "from": from_header,
            "subject": subject,
            "date": date,
            "body": body,
            "references": msg.get("References", ""),
            "in_reply_to": msg.get("In-Reply-To", ""),
        })

    imap.logout()
    logger.info("IMAP: fetched %d unread messages", len(parsed))
    return parsed


def send_reply(
    service=None,
    original_message_id: str = "",
    thread_id: str = "",
    to: str = "",
    subject: str = "",
    body: str = "",
) -> dict:
    """Send a reply email via SMTP."""
    _check_credentials()

    msg = MIMEText(body, "plain", "utf-8")
    user, password = _get_credentials()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

    # Threading headers
    if thread_id:
        msg["In-Reply-To"] = thread_id
        msg["References"] = thread_id

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.sendmail(user, to, msg.as_string())

    logger.info("SMTP: reply sent to %s, subject: %s", to, subject)
    return {"status": "sent", "to": to}


def mark_as_read(service=None, message_id: str = "") -> None:
    """Mark a message as read (SEEN) via IMAP."""
    _check_credentials()

    user, password = _get_credentials()
    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(user, password)
    imap.select("INBOX")

    # Mark as seen
    imap.store(message_id.encode() if isinstance(message_id, str) else message_id,
               "+FLAGS", "\\Seen")
    imap.logout()


def extract_email_address(from_header: str) -> str:
    """Extract bare email from 'Name <email>' format."""
    if "<" in from_header and ">" in from_header:
        return from_header.split("<")[1].split(">")[0].strip().lower()
    return from_header.strip().lower()
