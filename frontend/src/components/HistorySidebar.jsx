export default function HistorySidebar({ history, onSelect }) {
  const formatTime = (iso) => {
    return new Date(iso).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <p className="sidebar-title">Recent Tickets</p>
      </div>

      {history.length === 0 ? (
        <div className="sidebar-empty">
          <p>No tickets yet.</p>
          <p style={{ marginTop: 6 }}>Submit your first ticket to see history here.</p>
        </div>
      ) : (
        history.map((item, i) => (
          <div className="history-item" key={i} onClick={() => onSelect(item)}>
            <p className="history-id">{item.ticket_id}</p>
            <p className="history-preview">{item.ticket_text}</p>
            <p className="history-time">{formatTime(item.timestamp)}</p>
          </div>
        ))
      )}
    </div>
  );
}