import { AlertCircle, Boxes, FileText, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:5000";

function KnowledgeBase() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/knowledge-base`).then(async (response) => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not load Knowledge Base statistics.");
      if (active) setStats(data);
    }).catch((loadError) => {
      if (active) setError(loadError.message || "Unable to reach the AI service.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refreshKey]);
  const refresh = () => { setLoading(true); setError(""); setRefreshKey((key) => key + 1); };

  return <div className="page-stack">
    <section className="page-intro"><div><div className="eyebrow">CHROMADB INDEX</div><h1>Knowledge Base</h1><p>Statistics read from the active persistent vector collection.</p></div><button className="secondary-button" onClick={refresh} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button></section>
    {error && <div className="notice error-notice" role="alert"><AlertCircle size={16} />{error}<button className="text-button" onClick={refresh}>Try again</button></div>}
    {loading && !stats ? <div className="table-panel empty-state"><span className="loading-spinner" /> Reading ChromaDB statistics…</div> : stats && <>
      <section className="stats-grid"><article className="stat-card"><span className="card-icon"><Boxes size={18} /></span><span className="card-label">Indexed chunks</span><strong>{stats.total_chunks}</strong><small>Vectors in the active collection</small></article><article className="stat-card"><span className="card-icon"><FileText size={18} /></span><span className="card-label">Indexed sources</span><strong>{stats.indexed_documents}</strong><small>Distinct source and document IDs</small></article><article className="stat-card"><span className="card-icon status-icon"><span className="status-dot" /></span><span className="card-label">Collection status</span><strong className="positive">Available</strong><small>Statistics returned by FastAPI</small></article></section>
      <section className="table-panel"><div className="table-toolbar"><div><strong>Indexed sources</strong><span>Grouped from Chroma chunk metadata</span></div><Boxes size={17} /></div>
        {!stats.documents?.length ? <div className="empty-state"><Boxes size={25} /><strong>No indexed content</strong><span>Upload a document from the Query page to populate this collection.</span></div> : <div className="document-list"><div className="kb-row kb-header"><span>INDEXED SOURCE</span><span>CHUNKS</span><span>DOCUMENT ID</span></div>{stats.documents.map((document, index) => <div className="kb-row" key={`${document.document_id || document.source}-${index}`}><div className="document-name"><span className="file-icon"><FileText size={16} /></span><strong>{document.source.split(/[\\/]/).pop()}</strong></div><span><strong className="chunk-count">{document.chunks}</strong> chunks</span><code>{document.document_id || "Legacy source"}</code></div>)}</div>}
      </section>
      <p className="page-footnote">Counts reflect chunks that currently exist in ChromaDB; upload registry records are listed separately on Documents.</p>
    </>}
  </div>;
}

export default KnowledgeBase;
