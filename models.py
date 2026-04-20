from typing import Optional, Literal
from pydantic import BaseModel, Field


# --- Input Models ---

class OrderContext(BaseModel):
    """
    Structured order data that comes in alongside the ticket.
    All fields except order_id are optional — real tickets are often incomplete.
    """
    order_id: str
    order_date: Optional[str] = None
    delivery_date: Optional[str] = None
    item_category: Optional[Literal[
        "perishable", "electronics", "apparel", "hygiene",
        "furniture", "books", "final_sale", "other"
    ]] = None
    fulfillment_type: Optional[Literal["first-party", "marketplace"]] = None
    shipping_region: Optional[str] = None
    order_status: Optional[Literal[
        "placed", "shipped", "delivered", "returned", "cancelled"
    ]] = None
    payment_method: Optional[str] = None


class TicketInput(BaseModel):
    """Everything the system needs to process a support ticket."""
    ticket_text: str = Field(description="raw customer message")
    order: OrderContext


# --- Output Models ---

class TriageResult(BaseModel):
    issue_type: Literal[
        "refund", "shipping", "payment", "promo",
        "fraud", "dispute", "cancellation", "other"
    ]
    confidence: Literal["High", "Med", "Low"]
    missing_info: list[str] = []
    clarifying_questions: list[str] = []
    key_facts: str


class Citation(BaseModel):
    source_file: str
    chunk_id: str
    excerpt: str


class ResolutionOutput(BaseModel):
    """
    Full structured output for a resolved ticket.
    This is what gets saved to outputs/ and returned to the caller.
    """
    classification: str
    clarifying_questions: list[str] = []
    decision: Literal["approve", "deny", "partial", "escalate"]
    rationale: str
    citations: list[Citation]
    customer_response: str
    internal_notes: str
    compliance_verdict: Literal["APPROVED", "NEEDS REWRITE", "ESCALATE"]
    issues_found: list[str] = []


# --- Evaluation Models ---

class EvalCase(BaseModel):
    """Single test case in the evaluation set."""
    case_id: str
    category: Literal["standard", "exception", "conflict", "not_in_policy"]
    ticket_input: TicketInput
    expected_decision: Literal["approve", "deny", "partial", "escalate"]
    notes: Optional[str] = None


class EvalResult(BaseModel):
    """Result of running one eval case through the system."""
    case_id: str
    category: str
    expected_decision: str
    actual_decision: Optional[str] = None
    compliance_verdict: Optional[str] = None
    has_citations: bool = False
    correct_escalation: Optional[bool] = None
    passed: bool = False
    raw_output: Optional[str] = None
