from pydantic import BaseModel, field_validator
from typing import Optional, Literal


class TicketInput(BaseModel):
    ticket_text: str
    order_id: Optional[str] = None
    ticket_id: Optional[str] = None

    @field_validator("ticket_text")
    @classmethod
    def ticket_text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("ticket_text cannot be empty")
        return v.strip()

    @field_validator("order_id")
    @classmethod
    def clean_order_id(cls, v):
        if v is not None:
            return v.strip() or None
        return v


class ResolutionResult(BaseModel):
    """
    Structured output returned by resolve_ticket() in crew.py.
    This is what api.py uses — no more keyword parsing of raw LLM text.
    """
    status: Literal["resolved", "escalated", "needs_review", "needs_info", "error"]
    verdict: Optional[str] = None          # APPROVED / NEEDS REWRITE / ESCALATE
    result: Optional[str] = None           # full resolution text
    customer_response: Optional[str] = None  # extracted customer-facing message
    decision: Optional[str] = None         # brief decision summary
    citations: Optional[list] = None       # list of cited policy chunks
    missing_fields: Optional[list] = None  # fields needed for needs_info
    message: Optional[str] = None          # human-readable status message
    error: Optional[str] = None            # error details if status=error


class ResolutionOutput(BaseModel):
    """Full API response shape returned to frontend."""
    ticket_id: str
    status: str
    verdict: Optional[str] = None
    result: Optional[str] = None
    customer_response: Optional[str] = None
    decision: Optional[str] = None
    order: Optional[dict] = None
    timestamp: str
    message: Optional[str] = None
    missing_fields: Optional[list] = None
    error: Optional[str] = None