"""SQLite audit log for all bot actions."""

import sqlite3
import os
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot.db")


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            sender_email TEXT,
            subject TEXT,
            classification TEXT,
            confidence REAL,
            authorized INTEGER,
            invoice_numbers TEXT,
            invoices_found TEXT,
            action_taken TEXT,
            response_sent TEXT,
            error TEXT,
            processing_time_ms INTEGER
        )
    """)
    conn.commit()
    conn.close()


def log_event(
    sender_email: str = "",
    subject: str = "",
    classification: str = "",
    confidence: float = 0.0,
    authorized: bool = False,
    invoice_numbers: str = "",
    invoices_found: str = "",
    action_taken: str = "",
    response_sent: str = "",
    error: str = "",
    processing_time_ms: int = 0,
):
    conn = _connect()
    conn.execute(
        """INSERT INTO audit_log
           (timestamp, sender_email, subject, classification, confidence,
            authorized, invoice_numbers, invoices_found, action_taken,
            response_sent, error, processing_time_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().isoformat(),
            sender_email,
            subject,
            classification,
            confidence,
            int(authorized),
            invoice_numbers,
            invoices_found,
            action_taken,
            response_sent,
            error,
            processing_time_ms,
        ),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 50) -> list[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_logs_filtered(
    date_from: str = "", date_to: str = "", sender: str = ""
) -> list[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM audit_log WHERE 1=1"
    params: list = []
    if date_from:
        query += " AND timestamp >= ?"
        params.append(date_from)
    if date_to:
        query += " AND timestamp <= ?"
        params.append(date_to + "T23:59:59")
    if sender:
        query += " AND sender_email LIKE ?"
        params.append(f"%{sender}%")
    query += " ORDER BY id DESC LIMIT 200"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]
