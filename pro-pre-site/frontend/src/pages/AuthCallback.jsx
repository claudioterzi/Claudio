import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api } from "@/lib/api";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = React.useRef(false);

  React.useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = location.hash || window.location.hash;
    const m = hash.match(/session_id=([^&]+)/);
    if (!m) { navigate("/login", { replace: true }); return; }
    const session_id = m[1];

    api.post("/auth/session", { session_id })
      .then(r => {
        // Determine target based on saved redirect URL or default
        const target = window.location.pathname.includes("mon-espace") ? "/mon-espace" : "/admin";
        window.history.replaceState(null, "", target);
        navigate(target, { replace: true, state: { user: r.data } });
      })
      .catch(() => navigate("/login", { replace: true }));
  }, [navigate, location.hash]);

  return (
    <div className="section">
      <div className="container-narrow max-w-md text-center" data-testid="auth-callback">
        <p className="text-slate-500">…</p>
      </div>
    </div>
  );
}
