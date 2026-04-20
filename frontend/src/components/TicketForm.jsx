import { useState } from "react";

const DEFAULT_ORDER = {
  order_id: "",
  order_date: "",
  delivery_date: "",
  item_category: "electronics",
  fulfillment_type: "first-party",
  shipping_region: "India",
  order_status: "delivered",
  payment_method: "UPI",
};

export default function TicketForm({ onSubmit, loading }) {
  const [ticketText, setTicketText] = useState("");
  const [order, setOrder] = useState(DEFAULT_ORDER);
  const [showOrder, setShowOrder] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!ticketText.trim()) return;
    onSubmit({
      ticket_text: ticketText,
      order: order,
      ticket_id: order.order_id || undefined,
    });
  };

  const updateOrder = (key, val) => {
    setOrder(prev => ({ ...prev, [key]: val }));
  };

  return (
    <div className="form-card">
      <h2 className="form-title">Submit Support Ticket</h2>
      <p className="form-subtitle">Describe the customer issue and our AI agents will resolve it using Bazario policy.</p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Customer Issue *</label>
          <textarea
            className="form-textarea"
            placeholder="e.g. My order arrived 3 days late and the chocolates are completely melted. I want a full refund..."
            value={ticketText}
            onChange={e => setTicketText(e.target.value)}
            required
            rows={4}
          />
        </div>

        <div
          className="form-section"
          style={{ cursor: "pointer" }}
          onClick={() => setShowOrder(!showOrder)}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <p className="form-section-title">Order Context (optional)</p>
            <span style={{ fontSize: 13, color: "var(--muted)" }}>{showOrder ? "▲ hide" : "▼ show"}</span>
          </div>
        </div>

        {showOrder && (
          <>
            <div className="form-grid" style={{ marginTop: 14 }}>
              <div className="form-group">
                <label className="form-label">Order ID</label>
                <input
                  className="form-input"
                  placeholder="ORD-2026-001"
                  value={order.order_id}
                  onChange={e => updateOrder("order_id", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Payment Method</label>
                <select
                  className="form-select"
                  value={order.payment_method}
                  onChange={e => updateOrder("payment_method", e.target.value)}
                >
                  <option>UPI</option>
                  <option>Credit Card</option>
                  <option>Debit Card</option>
                  <option>Net Banking</option>
                  <option>COD</option>
                  <option>Wallet</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Order Date</label>
                <input
                  className="form-input"
                  type="date"
                  value={order.order_date}
                  onChange={e => updateOrder("order_date", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Delivery Date</label>
                <input
                  className="form-input"
                  type="date"
                  value={order.delivery_date}
                  onChange={e => updateOrder("delivery_date", e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Item Category</label>
                <select
                  className="form-select"
                  value={order.item_category}
                  onChange={e => updateOrder("item_category", e.target.value)}
                >
                  <option value="electronics">Electronics</option>
                  <option value="perishable">Perishable</option>
                  <option value="apparel">Apparel</option>
                  <option value="hygiene">Hygiene</option>
                  <option value="furniture">Furniture</option>
                  <option value="books">Books</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Fulfillment Type</label>
                <select
                  className="form-select"
                  value={order.fulfillment_type}
                  onChange={e => updateOrder("fulfillment_type", e.target.value)}
                >
                  <option value="first-party">First-party (Bazario)</option>
                  <option value="marketplace">Marketplace Seller</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Shipping Region</label>
                <select
                  className="form-select"
                  value={order.shipping_region}
                  onChange={e => updateOrder("shipping_region", e.target.value)}
                >
                  <option>India</option>
                  <option>International</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Order Status</label>
                <select
                  className="form-select"
                  value={order.order_status}
                  onChange={e => updateOrder("order_status", e.target.value)}
                >
                  <option value="delivered">Delivered</option>
                  <option value="in_transit">In Transit</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="returned">Returned</option>
                </select>
              </div>
            </div>
          </>
        )}

        <button className="submit-btn" type="submit" disabled={loading || !ticketText.trim()}>
          {loading ? "Agents working..." : "Resolve Ticket →"}
        </button>
      </form>
    </div>
  );
}