import os
import json
import uuid
from datetime import datetime
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

load_dotenv()

# --- Startup checks ---
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

print("Loading Bazario policy knowledge base...")
docs = load_policies()
chunks = chunk_documents(docs)
vs = get_or_build_index(chunks)
print("Ready.")

HISTORY_FILE = Path("outputs/history.json")
OUTPUTS_DIR  = Path(cfg.outputs_dir)
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
ORDERS_FILE = Path("data/orders.json")


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_to_history(entry):
    history = load_history()
    history.insert(0, entry)
    history = history[:50]
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def load_orders():
    if ORDERS_FILE.exists():
        return json.loads(ORDERS_FILE.read_text())
    return {}


def lookup_order(order_id: str):
    return load_orders().get(order_id)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Bazario Support API",
        "policies_loaded": True,
        "index_loaded": True
    })


@app.route("/resolve", methods=["POST"])
def resolve():
    data = request.get_json()

    # --- Pydantic validation ---
    try:
        payload = TicketInput(**data)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Invalid request: {str(e)}"
        }), 400

    ticket_text = payload.ticket_text
    order_id    = payload.order_id
    ticket_id   = payload.ticket_id or f"TKT-{uuid.uuid4().hex[:8].upper()}"
    timestamp   = datetime.now().isoformat()

    # --- Order ID validation ---
    if not order_id or not order_id.strip():
        entry = {
            "ticket_id": ticket_id,
            "ticket_text": ticket_text,
            "status": "needs_info",
            "missing_fields": ["order_id"],
            "message": "Please provide a valid Order ID so we can look up your order details.",
            "result": None,
            "timestamp": timestamp
        }
        save_to_history(entry)
        return jsonify(entry), 200

    # --- Order lookup ---
    order = lookup_order(order_id.strip())
    if not order:
        entry = {
            "ticket_id": ticket_id,
            "ticket_text": ticket_text,
            "status": "needs_info",
            "missing_fields": ["order_id"],
            "message": f"Order ID '{order_id}' not found. Please check and try again.",
            "result": None,
            "timestamp": timestamp
        }
        save_to_history(entry)
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
        save_to_history(entry)

        # Save full resolution text to file
        out_path = Path(f"outputs/resolutions/{ticket_id}.txt")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if resolution.result:
            out_path.write_text(resolution.result)

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
        save_to_history(entry)
        return jsonify(entry), 500


@app.route("/history", methods=["GET"])
def history():
    return jsonify(load_history())


@app.route("/history/<ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    history = load_history()
    ticket = next((t for t in history if t["ticket_id"] == ticket_id), None)
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