const STATUS_STYLES = {
  resolved:     { color: "#16a34a", label: "Resolved" },
  escalated:    { color: "#dc2626", label: "Escalated" },
  needs_review: { color: "#d97706", label: "Needs Review" },
  needs_info:   { color: "#2563eb", label: "Needs Info" },
  error:        { color: "#dc2626", label: "Error" },
};

function formatTimestamp(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });
}

export default function ResolutionView({ resolution }) {
  const { status, result, message, missing_fields, ticket_id, timestamp, order } = resolution;
  const style = STATUS_STYLES[status] || { color: "var(--muted)", label: status };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(result || message || "");
  };

  // needs_info: show a clear info message, no empty box
  if (status === "needs_info") {
    return (
      <div className="resolution-card">
        <div className="resolution-header">
          <h3 className="resolution-title">Action Required</h3>
          <span className="ticket-badge">{ticket_id}</span>
        </div>
        <div className="resolution-body">
          <div style={{
            background: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: 8,
            padding: "16px 20px",
            color: "#1e40af",
            fontSize: 14,
            lineHeight: 1.6,
          }}>
            <strong>Missing information</strong>
            {missing_fields?.length > 0 && (
              <ul style={{ margin: "8px 0 0 0", paddingLeft: 20 }}>
                {missing_fields.map(f => <li key={f}>{f}</li>)}
              </ul>
            )}
            {message && <p style={{ marginTop: 10 }}>{message}</p>}
          </div>
          <div className="resolution-meta" style={{ marginTop: 16 }}>
            <div className="meta-item">
              Status <span style={{ color: style.color }}>{style.label}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="resolution-card">
      <div className="resolution-header">
        <h3 className="resolution-title">Resolution</h3>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span className="ticket-badge">{ticket_id}</span>
          <button
            onClick={copyToClipboard}
            style={{
              fontSize: 12,
              padding: "4px 10px",
              border: "1px solid var(--border)",
              borderRadius: 6,
              background: "var(--bg)",
              cursor: "pointer",
              color: "var(--muted)",
            }}
          >
            Copy
          </button>
        </div>
      </div>

      <div className="resolution-body">
        {/* Show order details that were actually fetched from DB */}
        {order && (
          <div style={{
            background: "#f8fafc",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "10px 16px",
            fontSize: 12,
            color: "var(--muted)",
            marginBottom: 16,
            display: "flex",
            gap: 16,
            flexWrap: "wrap",
          }}>
            <span>📦 {order.order_id}</span>
            <span>🏷 {order.item_category}</span>
            <span>🚚 {order.order_status}</span>
            <span>💳 {order.payment_method}</span>
            <span>📍 {order.shipping_region}</span>
          </div>
        )}

        <pre className="resolution-text">{result}</pre>

        <div className="resolution-meta">
          <div className="meta-item">
            {status === "escalated" ? "Escalated at" : "Resolved at"}{" "}
            <span>{formatTimestamp(timestamp)}</span>
          </div>
          <div className="meta-item">
            Status <span style={{ color: style.color }}>{style.label}</span>
          </div>
        </div>
      </div>
    </div>
  );
}