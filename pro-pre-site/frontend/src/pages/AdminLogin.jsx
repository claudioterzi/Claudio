import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { LogIn, Lock } from "lucide-react";

export default function AdminLogin() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [checking, setChecking] = React.useState(true);

  React.useEffect(() => {
    // If already logged in, redirect to /admin
    if (window.location.hash?.includes('session_id=')) return;
    api.get("/auth/me").then(r => {
      if (r.data?.is_admin) navigate("/admin", { replace: true });
      else if (r.data) navigate("/admin", { replace: true }); // will see access denied
    }).catch(()=>{}).finally(()=>setChecking(false));
  }, [navigate]);

  const login = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/admin";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="section">
      <div className="container-narrow max-w-md">
        <div className="card-clean p-8 text-center" data-testid="admin-login-card">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1B2845] text-white">
            <Lock className="h-6 w-6" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold text-navy">{t("admin.title")}</h1>
          <p className="mt-1 text-sm text-slate-500">{t("admin.login_hint")}</p>
          <button onClick={login} className="btn-primary mt-6 w-full justify-center" data-testid="admin-login-google" disabled={checking}>
            <LogIn className="h-4 w-4" /> {t("admin.login")}
          </button>
        </div>
      </div>
    </div>
  );
}
