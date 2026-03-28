"""LLM-based email classification — determines if email asks about invoice status."""

import json
import os
import re
import logging

import anthropic

from bot.config import load_config
from bot.sanitizer import sanitize, wrap_for_llm

logger = logging.getLogger(__name__)


def classify_email(subject: str, body: str) -> dict:
    """Classify an email using Claude.

    Returns:
        dict with keys: is_invoice_query (bool), invoice_numbers (list[str]), confidence (float)
    """
    config = load_config()
    safe_body = sanitize(body, max_length=config.get("max_email_length", 2000))
    wrapped = wrap_for_llm(f"Temat: {subject}\n\n{safe_body}")

    system_prompt = config.get("classification_prompt", "")

    try:
        api_key = config.get("anthropic_api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=config.get("anthropic_model", "claude-sonnet-4-20250514"),
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": wrapped}],
        )

        text = response.content[0].text.strip()
        # Try to parse JSON from the response
        result = _parse_classification(text)
        logger.info("Classification result: %s", result)
        return result

    except Exception as e:
        logger.error("Classification failed: %s", e)
        return {
            "is_invoice_query": False,
            "invoice_numbers": [],
            "confidence": 0.0,
            "error": str(e),
        }


def _parse_classification(text: str) -> dict:
    """Parse LLM classification response, handling various JSON formats."""
    # Try direct JSON parse
    try:
        data = json.loads(text)
        return {
            "is_invoice_query": bool(data.get("is_invoice_query", False)),
            "invoice_numbers": list(data.get("invoice_numbers", [])),
            "confidence": float(data.get("confidence", 0.0)),
        }
    except (json.JSONDecodeError, ValueError):
        pass

    # Try extracting JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            return {
                "is_invoice_query": bool(data.get("is_invoice_query", False)),
                "invoice_numbers": list(data.get("invoice_numbers", [])),
                "confidence": float(data.get("confidence", 0.0)),
            }
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: look for invoice numbers in text
    invoice_nums = re.findall(r"(?:FV|FA)[/\-]?\d{4}[/\-]?\d{1,4}", text, re.I)
    has_query = bool(invoice_nums) or "true" in text.lower()

    return {
        "is_invoice_query": has_query,
        "invoice_numbers": invoice_nums,
        "confidence": 0.5,
    }
