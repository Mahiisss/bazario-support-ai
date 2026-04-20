import { useState } from "react";
import TicketForm from "./components/TicketForm";
import ResolutionView from "./components/ResolutionView";
import HistorySidebar from "./components/HistorySidebar";
import AgentProgress from "./components/AgentProgress";
import "./App.css";

export default function App() {
  const [resolution, setResolution] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState(null);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const agents = [
    { id: "triage", label: "Triage Agent", desc: "Classifying ticket" },
    { id: "retriever", label: "Policy Retriever", desc: "Searching knowledge base" },
    { id: "writer", label: "Resolution Writer", desc: "Drafting resolution" },
    { id: "compliance", label: "Compliance Agent", desc: "Verifying citations" },
    { id: "escalation", label: "Escalation Agent", desc: "Finalizing report" },
  ];

  const simulateProgress = () => {
    // simulate agent progress since we can't stream from Flask easily
    const delays = [2000, 5000, 9000, 11000, 13000];
    agents.forEach((agent, i) => {
      setTimeout(() => setActiveAgent(agent.id), delays[i]);
      setTimeout(() => {
        setCompletedAgents(prev => [...prev, agent.id]);
        if (i < agents.length - 1) setActiveAgent(null);
      }, delays[i] + 1800);
    });
  };

  const handleSubmit = async (ticketData) => {
    setLoading(true);
    setResolution(null);
    setError(null);
    setActiveAgent(null);
    setCompletedAgents([]);

    simulateProgress();

    try {
      const res = await fetch("http://localhost:5000/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ticketData),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Something went wrong");

      setResolution(data);
      setHistory(prev => [data, ...prev].slice(0, 20));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setActiveAgent(null);
    }
  };

  const loadFromHistory = (item) => {
    setResolution(item);
    setCompletedAgents(agents.map(a => a.id));
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">B</span>
            <span className="logo-text">Bazario</span>
            <span className="logo-tag">Support AI</span>
          </div>
          <div className="header-meta">
            <span className="status-dot" />
            <span className="status-text">5 agents online</span>
          </div>
        </div>
      </header>

      <main className="main">
        <HistorySidebar history={history} onSelect={loadFromHistory} />

        <div className="center">
          <TicketForm onSubmit={handleSubmit} loading={loading} />

          {(loading || completedAgents.length > 0) && (
            <AgentProgress
              agents={agents}
              activeAgent={activeAgent}
              completedAgents={completedAgents}
              loading={loading}
            />
          )}

          {error && (
            <div className="error-box">
              <span className="error-icon">!</span>
              <p>{error}</p>
            </div>
          )}

          {resolution && !loading && (
            <ResolutionView resolution={resolution} />
          )}
        </div>
      </main>
    </div>
  );
}