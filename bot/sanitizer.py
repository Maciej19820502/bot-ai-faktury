"""Input sanitization — defends against prompt injection."""

import re

# Patterns that attempt to override system instructions
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", re.I),
    re.compile(r"(system|assistant)\s*:", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"forget\s+(everything|all|your)\s+", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"<\s*/?\s*(system|prompt|instruction)", re.I),
    re.compile(r"\[INST\]", re.I),
    re.compile(r"```\s*(system|prompt)", re.I),
    re.compile(r"act\s+as\s+(if\s+you\s+are|a|an)\s+", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)\s+", re.I),
    re.compile(r"override\s+(your|the)\s+", re.I),
    re.compile(r"disregard\s+(your|the|all)\s+", re.I),
]

# Characters that should not appear in normal business emails
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize(text: str, max_length: int = 2000) -> str:
    """Clean email text for safe LLM processing."""
    if not text:
        return ""

    # Remove control characters
    text = _CONTROL_CHARS.sub("", text)

    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "\n[...treść skrócona]"

    # Flag injection attempts (replace with safe marker)
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[USUNIĘTO-PODEJRZANA-TREŚĆ]", text)

    return text.strip()


def wrap_for_llm(text: str) -> str:
    """Wrap user content in delimiters so the LLM treats it as data."""
    return f"<user_email>\n{text}\n</user_email>"
