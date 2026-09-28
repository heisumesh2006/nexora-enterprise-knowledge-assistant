import "../App.css";
import { ArrowUp, FileText, Paperclip, Sparkles, User, X } from "lucide-react";
import { useRef, useState } from "react";

const API_URL = "http://127.0.0.1:5000";
const suggestedQuestions = [
  "How many paid leave days do employees receive?",
  "What are the standard working hours?",
  "How do I apply for casual leave?",
];

function Query() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef(null);

  const sendQuestion = async (event) => {
    event?.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isLoading || isUploading) return;
    setMessages((current) => [...current, { id: `${Date.now()}-user`, role: "user", content: trimmedQuestion }]);
    setQuestion("");
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: trimmedQuestion }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to get a response from Nexora.");
      setMessages((current) => [...current, { id: `${Date.now()}-assistant`, role: "assistant", content: data.answer, citations: data.citations || [] }]);
    } catch (error) {
      setMessages((current) => [...current, { id: `${Date.now()}-error`, role: "assistant", content: error.message || "Unable to connect to the Nexora AI service.", error: true }]);
    } finally { setIsLoading(false); }
  };

  const uploadDocument = async (file) => {
    if (!file) return;
    const allowedTypes = ["application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowedTypes.includes(file.type) && ![".pdf", ".txt", ".docx"].includes(extension)) {
      setUploadError("Only PDF, TXT, and DOCX files are supported."); setUploadMessage(""); setSelectedFile(null); return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File size must not exceed 10 MB."); setUploadMessage(""); setSelectedFile(null); return;
    }
    setSelectedFile(file); setUploadError(""); setUploadMessage(""); setIsUploading(true);
    const formData = new FormData(); formData.append("document", file);
    try {
      const response = await fetch(`${API_URL}/api/documents/upload`, { method: "POST", body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to upload the document.");
      setUploadMessage(`${file.name} uploaded and indexed successfully.`);
    } catch (error) {
      setUploadError(error.message || "Unable to upload the document."); setUploadMessage("");
    } finally { setIsUploading(false); }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) uploadDocument(file);
    event.target.value = "";
  };

  return (
    <div className="query-layout">
      <section className="query-conversation" aria-live="polite">
        {messages.length === 0 ? (
          <div className="query-welcome"><div className="welcome-icon"><Sparkles size={23} /></div><div className="eyebrow">ASK YOUR KNOWLEDGE BASE</div><h1>What can I help you find?</h1><p>Answers are grounded in your uploaded company documents and include citations.</p>
            <div className="suggestions">{suggestedQuestions.map((suggestion) => <button key={suggestion} onClick={() => setQuestion(suggestion)}>{suggestion}</button>)}</div>
          </div>
        ) : <div className="conversation">{messages.map((message) => <div className={`message-row ${message.role}`} key={message.id}>
          <div className="message-avatar">{message.role === "user" ? <User size={15} /> : <Sparkles size={15} />}</div><div className="message-content"><div className="message-role">{message.role === "user" ? "You" : "Nexora"}</div><div className={`message-text${message.error ? " message-error" : ""}`}>{message.content}</div>
            {message.citations?.length > 0 && <div className="citations"><div className="citations-title">Sources</div>{message.citations.map((citation, index) => <div className="citation" key={`${citation.source}-${citation.page}-${index}`}><FileText size={13} /><span>{citation.source}{citation.page != null && ` — Page ${citation.page}`}</span></div>)}</div>}
          </div></div>)}{isLoading && <div className="message-row assistant"><div className="message-avatar"><Sparkles size={15} /></div><div className="message-content"><div className="message-role">Nexora</div><div className="message-text thinking">Searching your knowledge base…</div></div></div>}</div>}
      </section>

      <section className="query-composer-area" aria-label="Ask a question or upload a document">
        {selectedFile && <div className="upload-status"><div className="upload-file"><FileText size={15} /><span>{selectedFile.name}</span>{!isUploading && <button className="remove-file-button" onClick={() => { setSelectedFile(null); setUploadMessage(""); setUploadError(""); }} aria-label="Clear selected file"><X size={14} /></button>}</div>{isUploading && <span className="uploading-text">Indexing…</span>}</div>}
        {uploadMessage && <div className="notice success-notice" role="status">{uploadMessage}</div>}{uploadError && <div className="notice error-notice" role="alert">{uploadError}</div>}
        <form className="composer" onSubmit={sendQuestion}>
          <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx" onChange={handleFileChange} hidden />
          <button type="button" className="attach-button" onClick={() => fileInputRef.current?.click()} disabled={isUploading} aria-label="Upload PDF, TXT, or DOCX"><Paperclip size={18} /></button>
          <input type="text" value={question} onChange={(event) => setQuestion(event.target.value)} disabled={isLoading || isUploading} placeholder="Ask a question about your knowledge base…" aria-label="Your question" />
          <button type="submit" className="send-button" disabled={isLoading || isUploading || !question.trim()} aria-label="Send question"><ArrowUp size={18} /></button>
        </form>
        <div className="composer-hint">Upload PDF, TXT, or DOCX files. Documents are indexed before you ask about them.</div>
      </section>
    </div>
  );
}

export default Query;
