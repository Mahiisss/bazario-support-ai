export default function AgentProgress({ agents, activeAgent, completedAgents, loading }) {
  const getStatus = (agentId) => {
    if (completedAgents.includes(agentId)) return "done";
    if (activeAgent === agentId) return "active";
    return "pending";
  };

  const icons = {
    triage: "T",
    retriever: "R",
    writer: "W",
    compliance: "C",
    escalation: "E",
  };

  return (
    <div className="progress-card">
      <p className="progress-title">
        {loading ? "Processing ticket through agent pipeline..." : "Pipeline complete"}
      </p>

      <div className="agent-list">
        {agents.map((agent, i) => {
          const status = getStatus(agent.id);
          return (
            <div className="agent-row" key={agent.id}>
              <div className={`agent-icon ${status}`}>
                {status === "done" ? "✓" : icons[agent.id]}
              </div>
              <div className="agent-info">
                <p className="agent-name">{agent.label}</p>
                <p className="agent-desc">
                  {status === "active" ? agent.desc : status === "done" ? "Completed" : "Waiting..."}
                </p>
              </div>
              <span className={`agent-status ${status}`}>
                {status === "done" ? "Done" : status === "active" ? "Running" : "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}