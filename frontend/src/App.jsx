import "./App.css";
import {
  Activity,
  BookOpen,
  Boxes,
  FileText,
  LayoutDashboard,
  MessageSquare,
  Plus,
  Sparkles,
} from "lucide-react";
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Documents from "./pages/Documents.jsx";
import KnowledgeBase from "./pages/KnowledgeBase.jsx";
import NotFound from "./pages/NotFound.jsx";
import Query from "./pages/Query.jsx";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/query", label: "Query / Ask AI", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/knowledge-base", label: "Knowledge Base", icon: Boxes },
];

const pageDetails = {
  "/dashboard": ["Dashboard", "Your enterprise knowledge workspace at a glance."],
  "/query": ["Query / Ask AI", "Ask questions across your indexed knowledge."],
  "/documents": ["Documents", "Review files uploaded to your workspace."],
  "/knowledge-base": ["Knowledge Base", "Live indexing statistics from ChromaDB."],
};

function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [title, subtitle] = pageDetails[location.pathname] || ["Page not found", "That destination is not part of this workspace."];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink className="brand" to="/dashboard" aria-label="Nexora dashboard">
          <span className="brand-mark"><Sparkles size={19} /></span>
          <span><span className="brand-name">Nexora</span><span className="brand-subtitle">Enterprise Knowledge</span></span>
        </NavLink>

        <button className="new-chat-button" onClick={() => navigate("/query")}>
          <Plus size={17} /><span>New question</span>
        </button>

        <nav className="sidebar-section" aria-label="Main navigation">
          <div className="sidebar-label">Workspace</div>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} className={({ isActive }) => `sidebar-item${isActive ? " active" : ""}`} to={to}>
              <Icon size={17} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer"><span className="status-dot" /><span>Connected workspace</span></div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div><div className="topbar-title">{title}</div><div className="topbar-subtitle">{subtitle}</div></div>
          <div className="model-badge"><Activity size={15} /><span>AI knowledge assistant</span></div>
        </header>
        <div className="page-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/query" element={<Query />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/knowledge-base" element={<KnowledgeBase />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
        <footer className="app-footer"><BookOpen size={14} /> Nexora Enterprise Knowledge Assistant</footer>
      </main>
    </div>
  );
}

export default AppLayout;
