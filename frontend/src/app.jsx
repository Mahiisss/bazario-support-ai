import { useState } from "react";
import TicketForm from "./components/TicketForm";
import ResolutionView from "./components/ResolutionView";
import HistorySidebar from "./components/HistorySidebar";
import AgentProgress from "./components/AgentProgress";
import "./App.css";

const AGENTS = [
  { id: "triage",     label: "Triage Agent",       desc: "Classifying ticket" },
  { id: "retriever",  label: "Policy Retriever",    desc: "Searching knowledge base" },
  { id: "writer",     label: "Resolution Writer",   desc: "Drafting resolution" },
  { id: "compliance", label: "Compliance Agent",    desc: "Verifying citations" },
  { id: "escalation", label: "Escalation Agent",    desc: "Finalizing report" },
];

const ANIMATION_MS = 25000; // total animation duration in ms

export default function App() {
  const [resolution, setResolution]           = useState(null);
  const [loading, setLoading]                 = useState(false);
  const [activeAgent, setActiveAgent]         = useState(null);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [error, setError]                     = useState(null);
  const [history, setHistory]                 = useState([]);
  const [pipelineRan, setPipelineRan]         = useState(false);

  const simulateProgress = (agentsToShow) => {
    const delays = [2000, 5000, 9000, 11000, 13000];
    agentsToShow.forEach((agent, i) => {
      setTimeout(() => setActiveAgent(agent.id), delays[i]);
      setTimeout(() => {
        setCompletedAgents(prev => [...prev, agent.id]);
        if (i < agentsToShow.length - 1) setActiveAgent(null);
      }, delays[i] + 1800);
    });
  };

  const handleSubmit = async (ticketData) => {
    setLoading(true);
    setResolution(null);
    setError(null);
    setActiveAgent(null);
    setCompletedAgents([]);
    setPipelineRan(false);

    const startTime = Date.now();

    try {
      const res = await fetch("http://localhost:5000/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ticketData),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || "Something went wrong");

      if (data.status !== "needs_info") {
        setPipelineRan(true);
        const agentsToShow = data.status === "escalated"
          ? AGENTS
          : AGENTS.filter(a => a.id !== "escalation");
        simulateProgress(agentsToShow);

        // Wait for animation to finish before showing result
        const timeElapsed = Date.now() - startTime;
        const remaining = Math.max(0, ANIMATION_MS - timeElapsed);

        setTimeout(() => {
          setResolution(data);
          setHistory(prev => [data, ...prev].slice(0, 20));
          setLoading(false);
          setActiveAgent(null);
        }, remaining);

      } else {
        // needs_info — show immediately, no animation
        setResolution(data);
        setHistory(prev => [data, ...prev].slice(0, 20));
        setLoading(false);
        setActiveAgent(null);
      }

    } catch (err) {
      setError(err.message);
      setLoading(false);
      setActiveAgent(null);
    }
  };

  // const loadFromHistory = (item) => {
    // setResolution(item);
    // setPipelineRan(item.status !== "needs_info");
    // if (item.status !== "needs_info") {
      // const agentsToShow = item.status === "escalated"
        // ? AGENTS
        // : AGENTS.filter(a => a.id !== "escalation");
      // setCompletedAgents(agentsToShow.map(a => a.id));
    // } else {
      // setCompletedAgents([]);
    // }
  // };


  const loadFromHistory = (item) => {
  setResolution(item);
  setError(null);        // ← add this line
  setPipelineRan(item.status !== "needs_info");
  if (item.status !== "needs_info") {
    const agentsToShow = item.status === "escalated"
      ? AGENTS
      : AGENTS.filter(a => a.id !== "escalation");
    setCompletedAgents(agentsToShow.map(a => a.id));
  } else {
    setCompletedAgents([]);
  }
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
            <span className="status-text">Support AI</span>
          </div>
        </div>
      </header>

      <main className="main">
        <HistorySidebar history={history} onSelect={loadFromHistory} />

        <div className="center">
          <TicketForm onSubmit={handleSubmit} loading={loading} />

          {pipelineRan && (loading || completedAgents.length > 0) && (
            <AgentProgress
              agents={AGENTS}
              activeAgent={activeAgent}
              completedAgents={completedAgents}
              loading={loading}
              status={resolution?.status}
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