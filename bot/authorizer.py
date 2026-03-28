"""Sender authorization — checks if sender's domain is allowed."""

from bot.config import load_config


def get_domain(email: str) -> str:
    """Extract domain from email address."""
    if "@" in email:
        return email.split("@")[-1].strip().lower()
    return ""


def is_authorized(sender_email: str) -> bool:
    """Check if sender's domain is in the allowed list."""
    config = load_config()
    domain = get_domain(sender_email)
    allowed = config.get("allowed_domains", {})
    return domain in allowed


def get_client_name(sender_email: str) -> str:
    """Get client name for authorized sender, or empty string."""
    config = load_config()
    domain = get_domain(sender_email)
    allowed = config.get("allowed_domains", {})
    return allowed.get(domain, "")
