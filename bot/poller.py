"""Background email polling loop — the core orchestration."""

import time
import logging
import re

from bot.config import load_config
from bot import gmail_client, classifier, authorizer, invoice_lookup, responder, sanitizer, logger_db

logger = logging.getLogger(__name__)


def process_single_message(msg: dict, service) -> None:
    """Process a single email message through the full pipeline."""
    start = time.time()
    sender_full = msg.get("from", "")
    sender_email = gmail_client.extract_email_address(sender_full)
    subject = msg.get("subject", "")
    body = msg.get("body", "")
    msg_id = msg.get("id", "")
    thread_id = msg.get("thread_id", "")

    config = load_config()
    log_data = {
        "sender_email": sender_email,
        "subject": subject,
    }

    try:
        # Step 1: Sanitize input
        safe_body = sanitizer.sanitize(body, config.get("max_email_length", 2000))

        # Step 2: Classify email
        classification = classifier.classify_email(subject, safe_body)
        log_data["classification"] = "invoice_query" if classification["is_invoice_query"] else "other"
        log_data["confidence"] = classification.get("confidence", 0.0)

        if not classification["is_invoice_query"]:
            gmail_client.mark_as_read(service, msg_id)
            log_data["action_taken"] = "skipped_not_invoice_query"
            _log_final(log_data, start)
            return

        # Step 3: Authorize sender
        is_auth = authorizer.is_authorized(sender_email)
        log_data["authorized"] = is_auth
        client_name = authorizer.get_client_name(sender_email)

        if not is_auth:
            gmail_client.mark_as_read(service, msg_id)
            log_data["action_taken"] = "ignored_unauthorized"
            _log_final(log_data, start)
            return

        # Step 4: Look up invoices
        invoice_numbers = classification.get("invoice_numbers", [])
        log_data["invoice_numbers"] = ", ".join(invoice_numbers)

        found = []
        not_found = []
        for num in invoice_numbers:
            record = invoice_lookup.search_invoice(num)
            if record:
                found.append(record)
            else:
                not_found.append(num)

        log_data["invoices_found"] = ", ".join(inv.numer_faktury for inv in found)

        # Step 5: Check for overdue invoices of this client
        overdue = []
        if client_name:
            overdue = invoice_lookup.get_overdue_invoices_for_client(client_name)
            # Exclude already-found invoices from overdue list
            found_nums = {inv.numer_faktury for inv in found}
            overdue = [o for o in overdue if o.numer_faktury not in found_nums]

        # Step 6: Generate response
        reply_body = responder.generate_response(
            original_subject=subject,
            original_body_sanitized=safe_body,
            invoices_found=found,
            invoices_not_found=not_found,
            overdue_invoices=overdue,
            authorized=True,
            client_name=client_name,
        )

        # Step 7: Send reply to client
        gmail_client.send_reply(
            service, msg_id, thread_id, sender_email, subject, reply_body
        )

        # Step 8: Escalate if invoices not found or query not about specific invoice
        if not_found or not invoice_numbers:
            escalation_email = config.get("escalation_email", "")
            if escalation_email:
                esc_body = (
                    f"Eskalacja zapytania od: {sender_email} ({client_name})\n"
                    f"Temat: {subject}\n\n"
                    f"Treść zapytania:\n{safe_body[:1000]}\n\n"
                    f"Faktury nieznalezione: {', '.join(not_found) if not_found else 'brak numeru faktury w zapytaniu'}\n"
                    f"Faktury znalezione: {', '.join(inv.numer_faktury for inv in found) if found else 'brak'}\n"
                )
                gmail_client.send_reply(
                    service, "", "", escalation_email,
                    f"[ESKALACJA] {subject}", esc_body
                )
                logger.info("Escalation sent to %s", escalation_email)

        gmail_client.mark_as_read(service, msg_id)

        log_data["action_taken"] = "replied" if found else "replied+escalated"
        log_data["response_sent"] = reply_body[:500]
        _log_final(log_data, start)

        logger.info("Processed message from %s — %d found, %d not found",
                     sender_email, len(found), len(not_found))

    except Exception as e:
        logger.exception("Error processing message from %s: %s", sender_email, e)
        log_data["action_taken"] = "error"
        log_data["error"] = str(e)[:500]
        _log_final(log_data, start)
        # Still mark as read to avoid reprocessing loop
        try:
            gmail_client.mark_as_read(service, msg_id)
        except Exception:
            pass


def poll_once(service=None) -> int:
    """Run one polling cycle. Returns number of messages processed."""
    try:
        if service is None:
            service = gmail_client.authenticate()

        messages = gmail_client.get_unread_messages(service)
        logger.info("Poll: found %d unread messages", len(messages))

        for msg in messages:
            process_single_message(msg, service)

        return len(messages)

    except Exception as e:
        logger.exception("Poll cycle failed: %s", e)
        return 0


def _log_final(data: dict, start_time: float):
    """Write final log entry."""
    elapsed = int((time.time() - start_time) * 1000)
    logger_db.log_event(
        sender_email=data.get("sender_email", ""),
        subject=data.get("subject", ""),
        classification=data.get("classification", ""),
        confidence=data.get("confidence", 0.0),
        authorized=data.get("authorized", False),
        invoice_numbers=data.get("invoice_numbers", ""),
        invoices_found=data.get("invoices_found", ""),
        action_taken=data.get("action_taken", ""),
        response_sent=data.get("response_sent", ""),
        error=data.get("error", ""),
        processing_time_ms=elapsed,
    )
