import json
import argparse
from pathlib import Path

from core.ingestion import load_policies
from core.chunker import chunk_documents
from core.vectorstore import get_or_build_index
from crew import resolve_ticket


OUTPUT_DIR = Path("outputs/resolutions")


def save_result(ticket_id: str, result: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{ticket_id}.txt"
    out_path.write_text(result, encoding="utf-8")
    print(f"Result saved to {out_path}")


def run(ticket: str, order: dict, ticket_id: str = "ticket_001", verbose: bool = True):
    # build or load the vector index
    docs = load_policies()
    chunks = chunk_documents(docs)
    vs = get_or_build_index(chunks)

    print(f"\nProcessing ticket: {ticket_id}")
    print(f"Ticket: {ticket}\n")

    result = resolve_ticket(ticket, order, vs, verbose=verbose)

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(result)

    save_result(ticket_id, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a support ticket through the agent pipeline.")
    parser.add_argument("--ticket", type=str, help="Path to a JSON file with ticket + order")
    parser.add_argument("--quiet", action="store_true", help="Suppress agent verbose output")
    args = parser.parse_args()

    if args.ticket:
        # load from file if provided
        data = json.loads(Path(args.ticket).read_text())
        ticket_text = data["ticket_text"]
        order = data["order"]
        ticket_id = data.get("ticket_id", "ticket_001")
    else:
        # default test case — melted chocolates
        ticket_text = (
            "My order arrived 3 days late and the chocolates are completely melted. "
            "I want a full refund but don't want to return them since they're ruined."
        )
        order = {
            "order_id": "ORD-2026-00123",
            "order_date": "2026-03-20",
            "delivery_date": "2026-03-28",
            "item_category": "perishable",
            "fulfillment_type": "first-party",
            "shipping_region": "India",
            "order_status": "delivered",
            "payment_method": "UPI",
        }
        ticket_id = "ORD-2026-00123"

    run(ticket_text, order, ticket_id=ticket_id, verbose=not args.quiet)
