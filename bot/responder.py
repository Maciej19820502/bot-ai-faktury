"""Response generation — creates email replies using LLM."""

import os
import logging

import anthropic

from bot.config import load_config
from bot.sanitizer import wrap_for_llm
from bot.invoice_lookup import InvoiceRecord

logger = logging.getLogger(__name__)


def generate_response(
    original_subject: str,
    original_body_sanitized: str,
    invoices_found: list[InvoiceRecord],
    invoices_not_found: list[str],
    overdue_invoices: list[InvoiceRecord],
    authorized: bool,
    client_name: str = "",
) -> str:
    """Generate a response email using Claude.

    Returns the response text body.
    """
    config = load_config()

    # Build context for the LLM
    if not authorized:
        return _unauthorized_response()

    context_parts = []

    if invoices_found:
        context_parts.append("ZNALEZIONE FAKTURY:")
        for inv in invoices_found:
            context_parts.append(inv.to_display())
            context_parts.append("")

    if invoices_not_found:
        context_parts.append("FAKTURY NIEZNALEZIONE W SYSTEMIE:")
        for num in invoices_not_found:
            context_parts.append(f"  - {num}")
        context_parts.append("")

    if overdue_invoices:
        context_parts.append("DODATKOWA INFORMACJA — FAKTURY PRZETERMINOWANE TEGO KLIENTA:")
        for inv in overdue_invoices:
            context_parts.append(f"  - {inv.numer_faktury}: {inv.kwota} {inv.waluta}, termin: {inv.termin_platnosci}")
        context_parts.append("")

    invoice_context = "\n".join(context_parts)
    original_wrapped = wrap_for_llm(f"Temat: {original_subject}\n\n{original_body_sanitized}")

    system_prompt = config.get("response_prompt", "")
    tone = config.get("response_tone", "profesjonalny")
    system_prompt += f"\n\nTon odpowiedzi: {tone}"

    if client_name:
        system_prompt += f"\nKlient: {client_name}"

    user_message = f"""Dane fakturowe:
{invoice_context}

Oryginalna wiadomość klienta:
{original_wrapped}

Napisz odpowiedź e-mail."""

    try:
        api_key = config.get("anthropic_api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=config.get("anthropic_model", "claude-sonnet-4-20250514"),
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()

    except Exception as e:
        logger.error("Response generation failed: %s", e)
        return _fallback_response(invoices_found, invoices_not_found)


def _unauthorized_response() -> str:
    return (
        "Szanowni Państwo,\n\n"
        "Dziękujemy za wiadomość. Niestety, nie jesteśmy w stanie zweryfikować "
        "uprawnień nadawcy do uzyskania informacji o statusie faktur.\n\n"
        "Prosimy o kontakt z działem rozrachunków pod adresem: ap-team@company.com\n\n"
        "Z poważaniem,\n"
        "Bot AI — Dział Rozrachunków"
    )


def _fallback_response(
    found: list[InvoiceRecord], not_found: list[str]
) -> str:
    """Simple template fallback if LLM is unavailable."""
    lines = ["Szanowni Państwo,\n"]

    if found:
        lines.append("Informacja o statusie faktur:\n")
        for inv in found:
            lines.append(
                f"• {inv.numer_faktury} — Status: {inv.status}, "
                f"Kwota: {inv.kwota} {inv.waluta}, "
                f"Termin płatności: {inv.termin_platnosci}"
            )
            if inv.data_platnosci:
                lines.append(f"  Data płatności: {inv.data_platnosci}")

    if not_found:
        lines.append("\nNastępujących faktur nie odnaleziono w systemie:")
        for num in not_found:
            lines.append(f"• {num}")
        lines.append("\nProsimy o kontakt z działem AP/AR w celu wyjaśnienia.")

    lines.append("\nZ poważaniem,\nBot AI — Dział Rozrachunków")
    return "\n".join(lines)
