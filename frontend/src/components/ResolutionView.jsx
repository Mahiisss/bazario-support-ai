export default function ResolutionView({ resolution }) {
  const timestamp = new Date(resolution.timestamp).toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  const copyToClipboard = () => {
    navigator.clipboard.writeText(resolution.result);
  };

  return (
    <div className="resolution-card">
      <div className="resolution-header">
        <h3 className="resolution-title">Resolution</h3>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span className="ticket-badge">{resolution.ticket_id}</span>
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
        <pre className="resolution-text">{resolution.result}</pre>

        <div className="resolution-meta">
          <div className="meta-item">
            Resolved at <span>{timestamp}</span>
          </div>
          <div className="meta-item">
            Status <span style={{ color: "var(--success)" }}>{resolution.status}</span>
          </div>
        </div>
      </div>
    </div>
  );
}