import { useState } from "react";

export default function TicketForm({ onSubmit, loading }) {
  const [ticketText, setTicketText] = useState("");
  const [orderId, setOrderId] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ticketText.trim()) return;
    const payload = { ticket_text: ticketText };
    if (orderId.trim()) {
      payload.order_id = orderId.trim();
    }
    onSubmit(payload);
  };

  return (
    <div className="form-card">
      <h2 className="form-title">Submit Support Ticket</h2>
      <p className="form-subtitle">
        Describe the customer issue and our AI agents will resolve it using Bazario policy.
      </p>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Customer Issue *</label>
          <textarea
            className="form-textarea"
            placeholder="e.g. My order arrived 3 days late and the item is damaged. I want a full refund."
            value={ticketText}
            onChange={e => setTicketText(e.target.value)}
            required
            rows={4}
            disabled={loading}
          />
        </div>
        <div className="form-group" style={{ marginTop: 14 }}>
          <label className="form-label">Order ID *</label>
          <input
            className="form-input"
            placeholder="e.g. ORD-2026-001"
            value={orderId}
            onChange={e => setOrderId(e.target.value)}
            disabled={loading}
          />
          <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
            Required to verify order details. Example orders: ORD-2026-001 to ORD-2026-008
          </p>
        </div>
        <button
          className="submit-btn"
          type="submit"
          disabled={loading || !ticketText.trim()}
        >
          {loading ? "Agents working..." : "Resolve Ticket →"}
        </button>
      </form>
    </div>
  );
}