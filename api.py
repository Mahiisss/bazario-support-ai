import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from core.ingestion import load_policies
from core.chunker import chunk_documents
from core.vectorstore import get_or_build_index
from crew import resolve_ticket
from models import TicketInput
from config.config import cfg
from database import init_db, save_ticket, get_history, get_ticket_by_id
load_dotenv()

# --- Startup checks ---
if not os.getenv("GROQ_API_KEY") and not os.getenv("GROQ_API_KEY_1"):
    raise RuntimeError("No Groq API key found. Set GROQ_API_KEY or GROQ_API_KEY_1 in .env")

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# --- Build vector index ---
print("Loading Bazario policy knowledge base...")
docs   = load_policies()
chunks = chunk_documents(docs)
vs     = get_or_build_index(chunks)
print("Ready.")

# --- Init database ---
init_db()

ORDERS_FILE = Path("data/orders.json")
OUTPUTS_DIR = Path(cfg.outputs_dir)


def load_orders():
    if ORDERS_FILE.exists():
        return json.loads(ORDERS_FILE.read_text())
    return {}


def lookup_order(order_id: str):
    return load_orders().get(order_id)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":          "ok",
        "service":         "Bazario Support API",
        "policies_loaded": True,
        "index_loaded":    True,
        "database":        "connected"
    })


@app.route("/resolve", methods=["POST"])
def resolve():
    data = request.get_json()

    try:
        payload = TicketInput(**data)
    except Exception as e:
        return jsonify({"status": "error", "error": f"Invalid request: {str(e)}"}), 400

    ticket_text = payload.ticket_text
    order_id    = payload.order_id
    ticket_id   = payload.ticket_id or f"TKT-{uuid.uuid4().hex[:8].upper()}"

    IST = timezone(timedelta(hours=5, minutes=30))
    timestamp = datetime.now(IST).isoformat()
 




    # --- Order ID validation ---
    if not order_id or not order_id.strip():
        entry = {
            "ticket_id":     ticket_id,
            "ticket_text":   ticket_text,
            "status":        "needs_info",
            "missing_fields": ["order_id"],
            "message":       "Please provide a valid Order ID so we can look up your order details.",
            "result":        None,
            "timestamp":     timestamp
        }
        save_ticket(entry)
        return jsonify(entry), 200

    # --- Order lookup ---
    order = lookup_order(order_id.strip())
    if not order:
        entry = {
            "ticket_id":     ticket_id,
            "ticket_text":   ticket_text,
            "status":        "needs_info",
            "missing_fields": ["order_id"],
            "message":       f"Order ID '{order_id}' not found. Please check and try again.",
            "result":        None,
            "timestamp":     timestamp
        }
        save_ticket(entry)
        return jsonify(entry), 200

    # --- Run agent pipeline ---
    try:
        resolution = resolve_ticket(ticket_text, order, vs, verbose=False)

        entry = {
            "ticket_id":         ticket_id,
            "ticket_text":       ticket_text,
            "order":             order,
            "status":            resolution.status,
            "verdict":           resolution.verdict,
            "result":            resolution.result,
            "customer_response": resolution.customer_response,
            "decision":          resolution.decision,
            "message":           resolution.message,
            "missing_fields":    resolution.missing_fields,
            "timestamp":         timestamp
        }
        save_ticket(entry)

        # Save resolution text to file
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        if resolution.result:
            (OUTPUTS_DIR / f"{ticket_id}.txt").write_text(resolution.result)

        return jsonify(entry), 200

    except Exception as e:
        entry = {
            "ticket_id":   ticket_id,
            "ticket_text": ticket_text,
            "order":       order,
            "status":      "error",
            "error":       str(e),
            "result":      None,
            "timestamp":   timestamp
        }
        save_ticket(entry)
        return jsonify(entry), 500


@app.route("/history", methods=["GET"])
def history():
    return jsonify(get_history(limit=50))


@app.route("/history/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket not found"}), 404
    return jsonify(ticket)


@app.route("/orders", methods=["GET"])
def list_orders():
    return jsonify(load_orders())


@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    order = lookup_order(order_id)
    if not order:
        return jsonify({"error": f"Order '{order_id}' not found"}), 404
    return jsonify(order)


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=5000)