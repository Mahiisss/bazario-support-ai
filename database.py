import os
import json
from datetime import datetime
from typing import Optional
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    """Create tables if they don't exist. Run once on startup."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id         TEXT PRIMARY KEY,
                    ticket_text       TEXT NOT NULL,
                    order_id          TEXT,
                    order_data        JSONB,
                    status            TEXT NOT NULL,
                    verdict           TEXT,
                    result            TEXT,
                    customer_response TEXT,
                    decision          TEXT,
                    message           TEXT,
                    missing_fields    JSONB,
                    timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_tickets_timestamp
                ON tickets (timestamp DESC);
            """)
        conn.commit()
    print("[DB] Tables ready.")


def save_ticket(entry: dict):
    """Insert or update a ticket in the database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tickets (
                    ticket_id, ticket_text, order_id, order_data,
                    status, verdict, result, customer_response,
                    decision, message, missing_fields, timestamp
                ) VALUES (
                    %(ticket_id)s, %(ticket_text)s, %(order_id)s, %(order_data)s,
                    %(status)s, %(verdict)s, %(result)s, %(customer_response)s,
                    %(decision)s, %(message)s, %(missing_fields)s, %(timestamp)s
                )
                ON CONFLICT (ticket_id) DO UPDATE SET
                    status            = EXCLUDED.status,
                    verdict           = EXCLUDED.verdict,
                    result            = EXCLUDED.result,
                    customer_response = EXCLUDED.customer_response,
                    decision          = EXCLUDED.decision,
                    message           = EXCLUDED.message,
                    missing_fields    = EXCLUDED.missing_fields,
                    timestamp         = EXCLUDED.timestamp
            """, {
                "ticket_id":         entry.get("ticket_id"),
                "ticket_text":       entry.get("ticket_text"),
                "order_id":          entry.get("order", {}).get("order_id") if entry.get("order") else None,
                "order_data":        json.dumps(entry.get("order")) if entry.get("order") else None,
                "status":            entry.get("status"),
                "verdict":           entry.get("verdict"),
                "result":            entry.get("result"),
                "customer_response": entry.get("customer_response"),
                "decision":          entry.get("decision"),
                "message":           entry.get("message"),
                "missing_fields":    json.dumps(entry.get("missing_fields")) if entry.get("missing_fields") else None,
                "timestamp":         entry.get("timestamp", datetime.now().isoformat()),
            })
        conn.commit()


def get_history(limit: int = 50) -> list:
    """Get last N tickets ordered by timestamp desc."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM tickets
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            return [_row_to_dict(row) for row in rows]


def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    """Get a specific ticket by ID."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM tickets WHERE ticket_id = %s", (ticket_id,))
            row = cur.fetchone()
            return _row_to_dict(row) if row else None


def _row_to_dict(row) -> dict:
    """Convert a database row to a clean dict."""
    if row is None:
        return {}
    d = dict(row)
    if isinstance(d.get("order_data"), str):
        d["order_data"] = json.loads(d["order_data"])
    if isinstance(d.get("missing_fields"), str):
        d["missing_fields"] = json.loads(d["missing_fields"])
    d["order"] = d.pop("order_data", None)
    if hasattr(d.get("timestamp"), "isoformat"):
        d["timestamp"] = d["timestamp"].isoformat()
    return d