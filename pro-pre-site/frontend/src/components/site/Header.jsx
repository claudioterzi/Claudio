import React from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Globe, Menu, X, User, LogIn, LogOut, LayoutDashboard, FileText, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import ShareButton from "@/components/site/ShareButton";

const LANGS = [
  { code: "fr", label: "FR" },
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
  { code: "nl", label: "NL" },
  { code: "it", label: "IT" },
];

export default function Header() {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = React.useState(false);
  const [langOpen, setLangOpen] = React.useState(false);
  const [accountOpen, setAccountOpen] = React.useState(false);
  const [user, setUser] = React.useState(null); // {email, name?, is_admin?, kind: 'google'|'client'}
  const location = useLocation();
  const navigate = useNavigate();

  React.useEffect(() => { setOpen(false); setAccountOpen(false); }, [location.pathname]);

  // Fetch auth state — prefer Google (has admin info) else fallback to client magic-link
  React.useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const r = await api.get("/auth/me");
        if (!cancel) setUser({ ...r.data, kind: "google" });
        return;
      } catch { /* not google */ }
      try {
        const r = await api.get("/client/me");
        if (!cancel) setUser({ email: r.data.email, is_admin: false, kind: "client" });
      } catch {
        if (!cancel) setUser(null);
      }
    })();
    return () => { cancel = true; };
  }, [location.pathname]);

  const items = [
    { to: "/#services", label: t("nav.services") },
    { to: "/#defi", label: t("nav.defi") },
    { to: "/reglement", label: t("nav.reglement"), isRoute: true },
    { to: "/#contact", label: t("nav.contact") },
  ];

  const doLogout = async () => {
    if (user?.kind === "google") await api.post("/auth/logout").catch(() => {});
    if (user?.kind === "client") await api.post("/client/logout").catch(() => {});
    setUser(null);
    setAccountOpen(false);
    navigate("/", { replace: true });
  };

  const initials = (user?.name || user?.email || "?").slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white/85 backdrop-blur">
      <div className="container-narrow flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2" data-testid="header-logo-link">
          <img src="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/89z1mmv7_4FE6D8C7-4FFC-421A-947D-FEC6CFFD80D7.png" alt="Pro-pre" className="h-12 w-auto" />
        </Link>

        <nav className="hidden md:flex items-center gap-7 text-sm font-medium">
          {items.map(i => (
            i.isRoute ? (
              <Link key={i.to} to={i.to} className="text-slate-700 hover:text-[#1B2845] transition" data-testid={`nav-${i.label.toLowerCase().replace(/\s/g,'-')}`}>{i.label}</Link>
            ) : (
              <a key={i.to} href={i.to} className="text-slate-700 hover:text-[#1B2845] transition" data-testid={`nav-${i.label.toLowerCase().replace(/\s/g,'-')}`}>{i.label}</a>
            )
          ))}
          <Link to="/booking" className="text-slate-700 hover:text-[#1B2845] transition" data-testid="nav-booking">{t("nav.booking")}</Link>
        </nav>

        <div className="flex items-center gap-2">
          {/* Share button */}
          <ShareButton variant="icon" className="hidden sm:flex" />

          {/* Language switcher */}
          <div className="relative">
            <button
              onClick={() => { setLangOpen(o => !o); setAccountOpen(false); }}
              className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50"
              data-testid="lang-switcher-btn"
            >
              <Globe className="h-4 w-4 text-[#5BA4D4]" />
              <span className="font-semibold">{i18n.language?.slice(0,2).toUpperCase() || "FR"}</span>
            </button>
            {langOpen && (
              <div className="absolute right-0 mt-2 w-32 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg" data-testid="lang-dropdown">
                {LANGS.map(l => (
                  <button
                    key={l.code}
                    onClick={() => { i18n.changeLanguage(l.code); setLangOpen(false); }}
                    className={`block w-full px-3 py-2 text-left text-sm hover:bg-slate-50 ${i18n.language===l.code ? 'text-[#5BA4D4] font-semibold' : 'text-slate-700'}`}
                    data-testid={`lang-option-${l.code}`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Account menu */}
          <div className="relative">
            {user ? (
              <button
                onClick={() => { setAccountOpen(o => !o); setLangOpen(false); }}
                className="flex items-center gap-2 rounded-lg border border-slate-200 px-2 py-2 text-sm hover:bg-slate-50"
                data-testid="header-account-btn"
                aria-label="Account"
              >
                <div className="h-6 w-6 rounded-full bg-[#5BA4D4] text-white text-xs font-bold flex items-center justify-center">
                  {initials}
                </div>
                <ChevronDown className="h-3 w-3 text-slate-400" />
              </button>
            ) : (
              <button
                onClick={() => { setAccountOpen(o => !o); setLangOpen(false); }}
                className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50"
                data-testid="header-login-btn"
              >
                <LogIn className="h-4 w-4 text-[#5BA4D4]" />
                <span className="hidden sm:inline font-medium">{t("nav.login")}</span>
              </button>
            )}
            {accountOpen && (
              <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg" data-testid="account-dropdown">
                {user ? (
                  <>
                    <div className="px-3 py-2 border-b border-slate-100 bg-slate-50">
                      <p className="text-xs text-slate-500">{t("nav.signed_in_as")}</p>
                      <p className="text-sm font-semibold text-navy truncate" data-testid="account-email">{user.email}</p>
                    </div>
                    <Link
                      to="/mon-espace"
                      className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                      data-testid="account-mon-espace"
                    >
                      <FileText className="h-4 w-4 text-[#5BA4D4]" />
                      {t("nav.mon_espace")}
                    </Link>
                    {user.is_admin && (
                      <Link
                        to="/admin"
                        className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                        data-testid="account-admin"
                      >
                        <LayoutDashboard className="h-4 w-4 text-[#5BA4D4]" />
                        {t("nav.admin_dashboard")}
                      </Link>
                    )}
                    <button
                      onClick={doLogout}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 border-t border-slate-100"
                      data-testid="account-logout"
                    >
                      <LogOut className="h-4 w-4 text-slate-400" />
                      {t("nav.logout")}
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      to="/mon-espace"
                      className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                      data-testid="account-login-client"
                    >
                      <User className="h-4 w-4 text-[#5BA4D4]" />
                      {t("nav.login_client")}
                    </Link>
                    <Link
                      to="/login"
                      className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 border-t border-slate-100"
                      data-testid="account-login-admin"
                    >
                      <LayoutDashboard className="h-4 w-4 text-[#5BA4D4]" />
                      {t("nav.login_admin")}
                    </Link>
                  </>
                )}
              </div>
            )}
          </div>

          <Link to="/booking" className="hidden sm:inline-flex btn-primary !py-2 !px-4 text-sm" data-testid="header-book-cta">
            {t("hero.cta_book")}
          </Link>

          <button className="md:hidden p-2" onClick={() => setOpen(o => !o)} data-testid="mobile-menu-btn">
            {open ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      {open && (
        <div className="md:hidden border-t border-slate-200 bg-white" data-testid="mobile-menu">
          <div className="container-narrow flex flex-col py-3 gap-1">
            {items.map(i => (
              i.isRoute ? (
                <Link key={i.to} to={i.to} className="px-2 py-2 text-slate-700">{i.label}</Link>
              ) : (
                <a key={i.to} href={i.to} className="px-2 py-2 text-slate-700">{i.label}</a>
              )
            ))}
            <Link to="/booking" className="px-2 py-2 text-slate-700">{t("nav.booking")}</Link>
            {user ? (
              <>
                <div className="px-2 py-1 mt-2 text-xs text-slate-500 border-t border-slate-100 pt-3">
                  {t("nav.signed_in_as")}: <b>{user.email}</b>
                </div>
                <Link to="/mon-espace" className="px-2 py-2 text-slate-700 flex items-center gap-2" data-testid="mobile-mon-espace">
                  <FileText className="h-4 w-4" /> {t("nav.mon_espace")}
                </Link>
                {user.is_admin && (
                  <Link to="/admin" className="px-2 py-2 text-slate-700 flex items-center gap-2" data-testid="mobile-admin">
                    <LayoutDashboard className="h-4 w-4" /> {t("nav.admin_dashboard")}
                  </Link>
                )}
                <button onClick={doLogout} className="px-2 py-2 text-left text-slate-700 flex items-center gap-2" data-testid="mobile-logout">
                  <LogOut className="h-4 w-4" /> {t("nav.logout")}
                </button>
              </>
            ) : (
              <>
                <Link to="/mon-espace" className="px-2 py-2 text-slate-700 flex items-center gap-2 border-t border-slate-100 mt-2 pt-3" data-testid="mobile-login-client">
                  <User className="h-4 w-4" /> {t("nav.login_client")}
                </Link>
                <Link to="/login" className="px-2 py-2 text-slate-700 flex items-center gap-2" data-testid="mobile-login-admin">
                  <LayoutDashboard className="h-4 w-4" /> {t("nav.login_admin")}
                </Link>
              </>
            )}
            <Link to="/booking" className="btn-primary mt-2 justify-center">{t("hero.cta_book")}</Link>
          </div>
        </div>
      )}
    </header>
  );
}
