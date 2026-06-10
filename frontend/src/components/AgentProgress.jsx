export default function AgentProgress({ agents, activeAgent, completedAgents, loading, status }) {
  const getStatus = (agentId) => {
    if (completedAgents.includes(agentId)) return "done";
    if (activeAgent === agentId) return "active";
    return "pending";
  };

  const icons = {
    triage:     "T",
    retriever:  "R",
    writer:     "W",
    compliance: "C",
    escalation: "E",
  };

  const titleText = () => {
    if (loading) return "Processing ticket through agent pipeline...";
    if (status === "escalated")    return "Pipeline complete — Escalated to human agent";
    if (status === "needs_review") return "Pipeline complete — Needs review";
    return "Pipeline complete";
  };

  return (
    <div className="progress-card">
      <p className="progress-title">{titleText()}</p>

      <div className="agent-list">
        {agents.map((agent) => {
          const s = getStatus(agent.id);
          return (
            <div className="agent-row" key={agent.id}>
              <div className={`agent-icon ${s}`}>
                {s === "done" ? "✓" : icons[agent.id]}
              </div>
              <div className="agent-info">
                <p className="agent-name">{agent.label}</p>
                <p className="agent-desc">
                  {s === "active" ? agent.desc : s === "done" ? "Completed" : agent.id === "escalation" && status === "resolved" ? "Not needed" : "Waiting..."}
                </p>
              </div>
              <span className={`agent-status ${s}`}>
                {s === "done" ? "Done" : s === "active" ? "Running" : "—"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}