import "./App.css";
import {
  ArrowUp,
  Bot,
  FileText,
  MessageSquare,
  Paperclip,
  Plus,
  Search,
  Sparkles,
  User,
  X,
} from "lucide-react";
import { useRef, useState } from "react";

const API_URL = "http://127.0.0.1:5000";

const suggestedQuestions = [
  "How many paid leave days do employees receive?",
  "What are the standard working hours?",
  "How do I apply for casual leave?",
];

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  const fileInputRef = useRef(null);

  const sendQuestion = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isLoading || isUploading) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setQuestion("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmedQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Failed to get a response from Nexora."
        );
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: data.answer,
          citations: data.citations || [],
        },
      ]);
    } catch (error) {
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: Date.now() + 1,
          role: "assistant",
          content:
            error.message ||
            "Unable to connect to the Nexora AI service.",
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const uploadDocument = async (file) => {
    if (!file) {
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "text/plain",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    const allowedExtensions = [".pdf", ".txt", ".docx"];
    const fileExtension = file.name
      .slice(file.name.lastIndexOf("."))
      .toLowerCase();

    if (
      !allowedTypes.includes(file.type) &&
      !allowedExtensions.includes(fileExtension)
    ) {
      setUploadError("Only PDF, TXT, and DOCX files are supported.");
      setUploadMessage("");
      setSelectedFile(null);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError("File size must not exceed 10 MB.");
      setUploadMessage("");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setUploadError("");
    setUploadMessage("");
    setIsUploading(true);

    const formData = new FormData();
    formData.append("document", file);

    try {
      const response = await fetch(
        `${API_URL}/api/documents/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Failed to upload the document."
        );
      }

      setUploadMessage(
        `${file.name} uploaded and indexed successfully.`
      );
      setUploadError("");
    } catch (error) {
      setUploadError(
        error.message || "Unable to upload the document."
      );
      setUploadMessage("");
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (file) {
      uploadDocument(file);
    }

    event.target.value = "";
  };

  const openFilePicker = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const removeSelectedFile = () => {
    setSelectedFile(null);
    setUploadMessage("");
    setUploadError("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendQuestion();
    }
  };

  const selectSuggestion = (suggestion) => {
    setQuestion(suggestion);
  };

  const startNewConversation = () => {
    setMessages([]);
    setQuestion("");
    setIsLoading(false);
    setSelectedFile(null);
    setUploadMessage("");
    setUploadError("");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={19} />
          </div>

          <div>
            <div className="brand-name">Nexora</div>
            <div className="brand-subtitle">
              Enterprise Knowledge
            </div>
          </div>
        </div>

        <button
          className="new-chat-button"
          onClick={startNewConversation}
        >
          <Plus size={18} />
          <span>New conversation</span>
        </button>

        <div className="sidebar-section">
          <div className="sidebar-label">Workspace</div>

          <button className="sidebar-item active">
            <MessageSquare size={17} />
            <span>Knowledge Assistant</span>
          </button>

          <button className="sidebar-item">
            <FileText size={17} />
            <span>Documents</span>
          </button>

          <button className="sidebar-item">
            <Search size={17} />
            <span>Search Knowledge</span>
          </button>
        </div>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <span>AI service online</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="topbar-title">
              Knowledge Assistant
            </div>

            <div className="topbar-subtitle">
              Ask questions across your enterprise knowledge base
            </div>
          </div>

          <div className="model-badge">
            <Bot size={16} />
            <span>Qwen 2.5 · Local</span>
          </div>
        </header>

        <section className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-icon">
                <Sparkles size={25} />
              </div>

              <h1>What can I help you find?</h1>

              <p>
                Ask Nexora about company policies, employee
                information, documents, and other internal
                knowledge.
              </p>

              <div className="suggestions">
                {suggestedQuestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => selectSuggestion(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="conversation">
              {messages.map((message) => (
                <div
                  className={`message-row ${message.role}`}
                  key={message.id}
                >
                  <div className="message-avatar">
                    {message.role === "user" ? (
                      <User size={16} />
                    ) : (
                      <Sparkles size={16} />
                    )}
                  </div>

                  <div className="message-content">
                    <div className="message-role">
                      {message.role === "user" ? "You" : "Nexora"}
                    </div>

                    <div
                      className={`message-text ${
                        message.error ? "message-error" : ""
                      }`}
                    >
                      {message.content}
                    </div>

                    {message.citations?.length > 0 && (
                      <div className="citations">
                        <div className="citations-title">
                          Sources
                        </div>

                        {message.citations.map((citation, index) => (
                          <div
                            className="citation"
                            key={`${citation.source}-${citation.page}-${index}`}
                          >
                            <FileText size={13} />

                            <span>
                              {citation.source}

                              {citation.page !== null &&
                                citation.page !== undefined &&
                                ` — Page ${citation.page}`}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="message-row assistant">
                  <div className="message-avatar">
                    <Sparkles size={16} />
                  </div>

                  <div className="message-content">
                    <div className="message-role">Nexora</div>

                    <div className="message-text thinking">
                      <span>Thinking</span>
                      <span className="thinking-dots">...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        <div className="composer-wrapper">
          {selectedFile && (
            <div className="upload-status">
              <div className="upload-file">
                <FileText size={15} />

                <span>
                  {selectedFile.name}
                </span>

                {!isUploading && (
                  <button
                    className="remove-file-button"
                    onClick={removeSelectedFile}
                    aria-label="Remove uploaded file"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>

              {isUploading && (
                <span className="uploading-text">
                  Indexing...
                </span>
              )}
            </div>
          )}

          {uploadMessage && (
            <div className="upload-success">
              {uploadMessage}
            </div>
          )}

          {uploadError && (
            <div className="upload-error">
              {uploadError}
            </div>
          )}

          <div className="composer">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.docx"
              onChange={handleFileChange}
              hidden
            />

            <button
              className="attach-button"
              onClick={openFilePicker}
              disabled={isUploading}
              aria-label="Upload document"
              title="Upload PDF, TXT, or DOCX"
            >
              <Paperclip size={19} />
            </button>

            <input
              type="text"
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              onKeyDown={handleKeyDown}
              disabled={isLoading || isUploading}
              placeholder="Ask a question about your knowledge base..."
            />

            <button
              className="send-button"
              onClick={sendQuestion}
              disabled={
                isLoading ||
                isUploading ||
                !question.trim()
              }
              aria-label="Send question"
            >
              <ArrowUp size={19} />
            </button>
          </div>

          <div className="composer-hint">
            Upload a document to add it to the knowledge base,
            then ask Nexora questions about it.
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;