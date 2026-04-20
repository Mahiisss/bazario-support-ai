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

load_dotenv()

app = Flask(__name__)
CORS(app)  # allow React frontend to call this API

# build vector index once on startup
print("Loading Bazario policy knowledge base...")
docs = load_policies()
chunks = chunk_documents(docs)
vs = get_or_build_index(chunks)
print("Ready.")

HISTORY_FILE = Path("outputs/history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_to_history(entry):
    history = load_history()
    history.insert(0, entry)
    history = history[:50]  # keep last 50 tickets
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Bazario Support API"})


@app.route("/resolve", methods=["POST"])
def resolve():
    data = request.get_json()

    if not data or "ticket_text" not in data:
        return jsonify({"error": "ticket_text is required"}), 400

    ticket_text = data["ticket_text"]
    order = data.get("order", {})
    ticket_id = data.get("ticket_id", f"TKT-{uuid.uuid4().hex[:8].upper()}")

    try:
        result = resolve_ticket(ticket_text, order, vs, verbose=False)

        # save result to file
        out_path = Path(f"outputs/resolutions/{ticket_id}.txt")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result)

        entry = {
            "ticket_id": ticket_id,
            "ticket_text": ticket_text,
            "order": order,
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "status": "resolved"
        }
        save_to_history(entry)

        return jsonify({
            "ticket_id": ticket_id,
            "result": result,
            "status": "resolved",
            "timestamp": entry["timestamp"]
        })

    except Exception as e:
        error_entry = {
            "ticket_id": ticket_id,
            "ticket_text": ticket_text,
            "order": order,
            "result": str(e),
            "timestamp": datetime.now().isoformat(),
            "status": "error"
        }
        save_to_history(error_entry)
        return jsonify({"error": str(e), "ticket_id": ticket_id}), 500


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)