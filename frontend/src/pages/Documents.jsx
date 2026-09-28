import { AlertCircle, FileText, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:5000";
const formatSize = (bytes) => bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
const formatDate = (date) => new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(date));

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/documents`).then(async (response) => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not load documents.");
      if (active) setDocuments(Array.isArray(data.documents) ? data.documents : []);
    }).catch((loadError) => {
      if (active) setError(loadError.message || "Unable to reach the document service.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [refreshKey]);
  const refresh = () => { setLoading(true); setError(""); setRefreshKey((key) => key + 1); };

  return <div className="page-stack">
    <section className="page-intro"><div><div className="eyebrow">WORKSPACE FILES</div><h1>Documents</h1><p>Files registered by the upload service.</p></div><button className="secondary-button" onClick={refresh} disabled={loading}><RefreshCw size={15} className={loading ? "spin" : ""} /> Refresh</button></section>
    {error && <div className="notice error-notice" role="alert"><AlertCircle size={16} />{error}<button className="text-button" onClick={refresh}>Try again</button></div>}
    <section className="table-panel"><div className="table-toolbar"><div><strong>Uploaded files</strong><span>{loading ? "Loading…" : `${documents.length} ${documents.length === 1 ? "file" : "files"}`}</span></div><FileText size={17} /></div>
      {loading ? <div className="empty-state"><span className="loading-spinner" /> Loading documents…</div> : error ? null : documents.length === 0 ? <div className="empty-state"><FileText size={25} /><strong>No documents yet</strong><span>Upload a PDF, TXT, or DOCX file from the Query page.</span></div> :
        <div className="document-list"><div className="document-row document-header"><span>NAME</span><span>TYPE</span><span>SIZE</span><span>UPLOADED</span></div>{documents.slice().reverse().map((document) => <div className="document-row" key={document.id}><div className="document-name"><span className="file-icon"><FileText size={16} /></span><span><strong>{document.originalName}</strong><small>{document.storedName}</small></span></div><span className="type-pill">{document.originalName.split(".").pop()?.toUpperCase() || document.type}</span><span>{formatSize(document.size)}</span><span>{formatDate(document.uploadedAt)}</span></div>)}</div>}
    </section>
    <p className="page-footnote">Upload records are shown as stored by the backend. Indexing counts are available on the Knowledge Base page.</p>
  </div>;
}

export default Documents;
