import { ArrowRight, Boxes, FileText, MessageSquare, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:5000";

function Dashboard() {
  const [documents, setDocuments] = useState(null);
  const [knowledge, setKnowledge] = useState(null);
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      fetch(`${API_URL}/api/documents`).then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Could not load documents.");
        return data.documents || [];
      }),
      fetch(`${API_URL}/api/knowledge-base`).then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Knowledge Base is unavailable.");
        return data;
      }),
    ]).then((results) => {
      if (!active) return;
      setDocuments(results[0].status === "fulfilled" ? results[0].value : null);
      setKnowledge(results[1].status === "fulfilled" ? results[1].value : null);
      setErrors(results.filter((result) => result.status === "rejected").map((result) => result.reason.message));
    });
    return () => { active = false; };
  }, []);

  const cards = [
    { label: "Uploaded documents", value: documents?.length ?? "—", note: documents === null ? "Could not load registry" : "Files in the upload registry", icon: FileText, to: "/documents" },
    { label: "Indexed chunks", value: knowledge?.total_chunks ?? "—", note: knowledge ? `${knowledge.indexed_documents} indexed sources` : "Knowledge Base unavailable", icon: Boxes, to: "/knowledge-base" },
    { label: "AI service", value: knowledge ? "Online" : "Unavailable", note: knowledge ? "Chroma statistics responding" : "Check the AI service connection", icon: Sparkles, to: "/query", state: Boolean(knowledge) },
  ];

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div className="hero-copy"><div className="eyebrow">ENTERPRISE KNOWLEDGE WORKSPACE</div><h1>Good to see you.</h1><p>Find answers in your company knowledge, manage uploaded files, and see what is indexed.</p>
          <Link className="primary-button" to="/query"><MessageSquare size={16} /> Ask AI <ArrowRight size={15} /></Link>
        </div>
        <div className="hero-orbit"><div className="orbit-ring" /><div className="orbit-core"><Sparkles size={30} /></div><span className="orbit-node node-one" /><span className="orbit-node node-two" /><span className="orbit-node node-three" /></div>
      </section>

      {errors.length > 0 && <div className="notice error-notice" role="alert">{errors.join(" ")}</div>}

      <section className="section-block">
        <div className="section-heading"><div><div className="eyebrow">WORKSPACE OVERVIEW</div><h2>At a glance</h2></div><span className="live-label"><span className="status-dot" /> Live data</span></div>
        <div className="overview-grid">
          {cards.map(({ label, value, note, icon: Icon, to, state }) => (
            <Link className="overview-card" key={label} to={to}>
              <div className="card-icon"><Icon size={18} /></div><div className="card-label">{label}</div><div className={`card-value${state === undefined ? "" : state ? " positive" : " negative"}`}>{value}</div><div className="card-note">{note}</div>
            </Link>
          ))}
        </div>
      </section>

      <section className="section-block"><div className="section-heading"><div><div className="eyebrow">GET STARTED</div><h2>Go to a workspace</h2></div></div>
        <div className="destination-grid">
          <Link className="destination-card" to="/query"><span className="destination-icon"><MessageSquare size={18} /></span><span><strong>Ask a question</strong><small>Get grounded answers with source citations.</small></span><ArrowRight size={16} /></Link>
          <Link className="destination-card" to="/documents"><span className="destination-icon"><FileText size={18} /></span><span><strong>Browse documents</strong><small>View files uploaded to the workspace.</small></span><ArrowRight size={16} /></Link>
          <Link className="destination-card" to="/knowledge-base"><span className="destination-icon"><Boxes size={18} /></span><span><strong>Explore the index</strong><small>Review real indexed sources and chunk counts.</small></span><ArrowRight size={16} /></Link>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
