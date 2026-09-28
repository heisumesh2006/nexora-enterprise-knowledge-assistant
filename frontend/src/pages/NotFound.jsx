import { ArrowLeft, Compass } from "lucide-react";
import { Link } from "react-router-dom";

function NotFound() {
  return <div className="not-found"><span className="not-found-icon"><Compass size={23} /></span><div className="eyebrow">404 · PAGE NOT FOUND</div><h1>This page isn’t in the workspace.</h1><p>Use the navigation to return to a Nexora page.</p><Link className="primary-button" to="/dashboard"><ArrowLeft size={15} /> Back to Dashboard</Link></div>;
}

export default NotFound;
