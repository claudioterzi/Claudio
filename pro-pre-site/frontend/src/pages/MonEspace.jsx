import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, API } from "@/lib/api";
import {
  Calendar,
  FileText,
  Check,
  LogIn,
  Loader2,
  Mail,
  LogOut,
  Download,
  Image as ImageIcon,
  Clock,
  Camera,
  MapPin,
  Sparkles,
  ChevronRight,
  Phone,
  Star,
  Upload,
  Shield,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

const STATUS_COLOR = {
  signed: "bg-blue-50 text-blue-700 border-blue-200",
  test_done: "bg-emerald-50 text-emerald-700 border-emerald-200",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  cancelled: "bg-slate-50 text-slate-500 border-slate-200",
};

async function resizeToBase64(file, maxDim = 1400, quality = 0.82) {
  const dataUrl = await new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
      const w = Math.round(img.width * scale);
      const h = Math.round(img.height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, w, h);
      resolve(canvas.toDataURL("image/jpeg", quality));
    };
    img.onerror = () => resolve(dataUrl);
    img.src = dataUrl;
  });
}

export default function MonEspace() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const [clientEmail, setClientEmail] = React.useState(null);
  const [googleUser, setGoogleUser] = React.useState(null);
  const [contracts, setContracts] = React.useState([]);
  const [bookings, setBookings] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [showRequest, setShowRequest] = React.useState(false);
  const [emailInput, setEmailInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [magicMode, setMagicMode] = React.useState("idle");
  const [uploadingPhoto, setUploadingPhoto] = React.useState({});

  const loadAll = React.useCallback(async () => {
    let email = null;
    let gUser = null;
    try {
      const meC = await api.get("/client/me");
      email = meC.data.email;
      setClientEmail(email);
    } catch { /* not client */ }
    try {
      const meG = await api.get("/auth/me");
      gUser = meG.data;
      setGoogleUser(gUser);
    } catch { /* not google */ }
    if (email || gUser?.email) {
      try {
        const cr = await api.get("/client/contracts");
        setContracts(cr.data.contracts || []);
      } catch { setContracts([]); }
      if (gUser) {
        try {
          const br = await api.get("/me/bookings");
          setBookings(br.data.bookings || []);
        } catch { setBookings([]); }
      }
    }
    setLoading(false);
  }, []);

  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get("token");
    if (token) {
      setMagicMode("verifying");
      api
        .get(`/client/verify-magic-link?token=${encodeURIComponent(token)}`)
        .then((r) => {
          setClientEmail(r.data.email);
          setMagicMode("ok");
          toast.success(t("me.login_success"));
          navigate("/mon-espace", { replace: true });
        })
        .catch((e) => {
          setMagicMode("idle");
          toast.error(e.response?.data?.detail || t("me.login_error"));
        })
        .finally(() => loadAll());
    } else {
      loadAll();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search]);

  const currentEmail = clientEmail || googleUser?.email;
  const currentName = googleUser?.name || (currentEmail?.split("@")[0] || "");
  const firstName = currentName.split(" ")[0] || "";

  const requestMagicLink = async () => {
    if (!emailInput.trim()) return;
    setSending(true);
    try {
      await api.post("/client/request-magic-link", {
        email: emailInput.trim(),
        language: i18n.language,
      });
      setMagicMode("sent");
      toast.success(t("me.magic_sent_toast"));
    } catch {
      toast.error(t("me.login_error"));
    } finally { setSending(false); }
  };

  const logout = async () => {
    if (googleUser) await api.post("/auth/logout").catch(() => {});
    if (clientEmail) await api.post("/client/logout").catch(() => {});
    setGoogleUser(null);
    setClientEmail(null);
    setContracts([]);
    setBookings([]);
    setShowRequest(false);
    setMagicMode("idle");
    navigate("/mon-espace", { replace: true });
  };

  const deleteMyData = async () => {
    const confirmed = window.confirm(t("me.gdpr_confirm"));
    if (!confirmed) return;
    try {
      const r = await api.delete("/client/my-data");
      const d = r.data?.deleted || {};
      toast.success(
        t("me.gdpr_success", {
          bookings: d.bookings ?? 0,
          contracts: d.contracts ?? 0,
          photos: d.photos ?? 0,
        }),
      );
      setTimeout(() => logout(), 1200);
    } catch (e) {
      const msg = e?.response?.data?.detail || t("admin.error");
      toast.error(msg);
    }
  };

  const googleLogin = () => {
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(window.location.origin + "/mon-espace")}`;
  };

  const rebookLike = (source) => {
    // source can be a contract or a booking; extract prefill data
    const state = {
      preselect: source.service_id || source.items?.[0]?.service_id || undefined,
      prefill: {
        full_name: source.full_name || source.client_name || "",
        phone: source.phone || source.client_phone || "",
        email: source.email || source.client_email || currentEmail || "",
        address: source.address || "",
        city: source.city || "Bruxelles",
        postal_code: source.postal_code || "",
      },
    };
    navigate("/booking", { state });
  };

  const uploadAfter = async (contractId, file) => {
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) {
      toast.error(t("defi_flow.photo_too_big"));
      return;
    }
    setUploadingPhoto((s) => ({ ...s, [contractId]: true }));
    try {
      const b64 = await resizeToBase64(file);
      await api.post(`/client/contracts/${contractId}/photo-after`, { photo_after_base64: b64 });
      toast.success(t("me.photo_after_sent"));
      const cr = await api.get("/client/contracts");
      setContracts(cr.data.contracts || []);
    } catch {
      toast.error(t("admin.error"));
    } finally {
      setUploadingPhoto((s) => ({ ...s, [contractId]: false }));
    }
  };

  if (loading || magicMode === "verifying") {
    return (
      <div className="section">
        <div className="container-narrow text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-[#5BA4D4]" />
          <p className="mt-4 text-slate-500 text-sm">{t("me.loading")}</p>
        </div>
      </div>
    );
  }

  if (!currentEmail) {
    return <LoginScreen
      showRequest={showRequest} setShowRequest={setShowRequest}
      emailInput={emailInput} setEmailInput={setEmailInput}
      sending={sending} magicMode={magicMode}
      requestMagicLink={requestMagicLink} googleLogin={googleLogin}
      t={t}
    />;
  }

  // Determine "Next appointment" — a booking with status not annulee/completee, sorted by date
  const upcoming = [...bookings]
    .filter((b) => b.status && !["annulee", "completee"].includes(b.status))
    .sort((a, b) => (a.date || "").localeCompare(b.date || ""))[0];
  const lastRebookSource = upcoming || bookings[0] || contracts[0];

  const hasAny = contracts.length > 0 || bookings.length > 0;

  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="flex justify-between items-center flex-wrap gap-3" data-testid="me-header">
          <div>
            <p className="eyebrow">Pro-pre</p>
            <h1 className="mt-1 text-3xl sm:text-4xl font-semibold text-navy">
              {t("me.welcome_back")} {firstName ? `${firstName} 👋` : "👋"}
            </h1>
            <p className="text-sm text-slate-500 mt-1">{currentEmail}</p>
          </div>
          <button onClick={logout} className="btn-outline !py-2 !px-4 text-sm" data-testid="me-logout">
            <LogOut className="h-4 w-4" /> {t("nav.logout")}
          </button>
        </div>

        {/* Next appointment hero card */}
        {upcoming ? (
          <div className="mt-8 rounded-2xl bg-gradient-to-br from-[#1B2845] to-[#2E4372] text-white p-6 shadow-xl" data-testid="me-next-hero">
            <div className="flex justify-between items-start flex-wrap gap-3">
              <div>
                <p className="text-xs uppercase tracking-widest text-[#5BA4D4] font-semibold">
                  {t("me.next_appointment")}
                </p>
                <p className="mt-2 text-3xl font-bold">{upcoming.date}</p>
                <p className="text-lg text-slate-200">{upcoming.time_slot}</p>
                <div className="mt-3 flex items-center gap-2 text-sm text-slate-300">
                  <MapPin className="h-4 w-4" />
                  {upcoming.address}, {upcoming.postal_code} {upcoming.city}
                </div>
                <div className="mt-2 flex items-center gap-2 text-sm text-slate-300">
                  <Sparkles className="h-4 w-4" />
                  {t("me.technician")}: <b className="text-white">Claudio Terzi</b>
                </div>
                <div className="mt-3 flex items-center gap-3">
                  <span className="px-3 py-1 rounded-full bg-white/10 text-xs font-medium">
                    {t(`admin.status.${upcoming.status}`)}
                  </span>
                  {upcoming.estimated_price > 0 && (
                    <span className="px-3 py-1 rounded-full bg-[#5BA4D4] text-white text-xs font-semibold">
                      €{upcoming.estimated_price}
                    </span>
                  )}
                </div>
              </div>
              <a href="tel:+33674932000" className="btn-outline !border-white/30 !text-white hover:!bg-white/10">
                <Phone className="h-4 w-4" /> {t("me.call_us")}
              </a>
            </div>
          </div>
        ) : hasAny ? (
          <NoUpcomingCard lastRebookSource={lastRebookSource} rebookLike={rebookLike} t={t} />
        ) : null}

        {/* Quick actions */}
        <div className="mt-8 grid sm:grid-cols-2 gap-3" data-testid="me-quick-actions">
          <button
            onClick={() => lastRebookSource ? rebookLike(lastRebookSource) : navigate("/booking")}
            className="card-clean p-5 text-left hover:border-[#5BA4D4] group flex items-center gap-4"
            data-testid="me-rebook-cta"
          >
            <div className="h-11 w-11 rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4] flex items-center justify-center flex-shrink-0">
              <Calendar className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-navy">{t("me.rebook_title")}</p>
              <p className="text-xs text-slate-500 mt-0.5">{t("me.rebook_sub")}</p>
            </div>
            <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-[#5BA4D4]" />
          </button>
          <button
            onClick={() => navigate("/defi")}
            className="card-clean p-5 text-left hover:border-[#5BA4D4] group flex items-center gap-4"
            data-testid="me-defi-cta"
          >
            <div className="h-11 w-11 rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4] flex items-center justify-center flex-shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-navy">{t("me.defi_title")}</p>
              <p className="text-xs text-slate-500 mt-0.5">{t("me.defi_sub")}</p>
            </div>
            <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-[#5BA4D4]" />
          </button>
        </div>

        {/* Contracts */}
        {contracts.length > 0 && (
          <div className="mt-12">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-[#5BA4D4]" />
              <h2 className="text-xl font-semibold text-navy">
                {t("me.my_contracts")}
              </h2>
              <span className="text-sm text-slate-500">({contracts.length})</span>
            </div>
            <div className="grid gap-4">
              {contracts.map((c) => (
                <ContractCard
                  key={c.id}
                  contract={c}
                  onRebook={() => rebookLike(c)}
                  onUpload={(f) => uploadAfter(c.id, f)}
                  uploading={uploadingPhoto[c.id]}
                  t={t}
                />
              ))}
            </div>
          </div>
        )}

        {/* Bookings history */}
        {bookings.length > 0 && (
          <div className="mt-12">
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="h-5 w-5 text-[#5BA4D4]" />
              <h2 className="text-xl font-semibold text-navy">{t("me.history_title")}</h2>
              <span className="text-sm text-slate-500">({bookings.length})</span>
            </div>
            <div className="grid gap-3">
              {bookings.map((b) => (
                <div key={b.id} className="card-clean p-4 flex flex-wrap justify-between items-center gap-3" data-testid={`me-booking-${b.id}`}>
                  <div className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                      b.status === "completee" ? "bg-emerald-100 text-emerald-600" :
                      b.status === "annulee" ? "bg-slate-100 text-slate-400" :
                      "bg-[#5BA4D4]/10 text-[#5BA4D4]"
                    }`}>
                      {b.status === "completee" ? <Check className="h-5 w-5" /> : <Calendar className="h-5 w-5" />}
                    </div>
                    <div>
                      <p className="font-medium text-navy">{b.date} · {b.time_slot}</p>
                      <p className="text-xs text-slate-500">
                        {b.city} · {t(`admin.status.${b.status}`)}
                        {b.estimated_price > 0 && ` · €${b.estimated_price}`}
                      </p>
                    </div>
                  </div>
                  {b.status !== "annulee" && (
                    <button
                      onClick={() => rebookLike(b)}
                      className="text-xs rounded-lg bg-[#5BA4D4]/10 text-[#5BA4D4] hover:bg-[#5BA4D4]/20 px-3 py-2 font-medium flex items-center gap-1"
                      data-testid={`me-rebook-${b.id}`}
                    >
                      {t("me.rebook_same")} <ChevronRight className="h-3 w-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {!hasAny && (
          <div className="mt-10 card-clean p-8 text-center" data-testid="me-empty">
            <Sparkles className="mx-auto h-10 w-10 text-[#5BA4D4]" />
            <h3 className="mt-4 text-xl font-semibold text-navy">{t("me.empty_title")}</h3>
            <p className="mt-2 text-slate-600">{t("me.empty_body")}</p>
            <button onClick={() => navigate("/defi")} className="btn-primary mt-6" data-testid="me-empty-cta">
              <Sparkles className="h-4 w-4" /> {t("me.book_defi")}
            </button>
          </div>
        )}

        {/* GDPR — Data control panel */}
        <div className="mt-14 rounded-2xl border border-slate-200 bg-slate-50 p-6" data-testid="me-gdpr-panel">
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-xl bg-white text-[#5BA4D4] flex items-center justify-center border border-slate-200 flex-shrink-0">
              <Shield className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-navy">{t("me.gdpr_title")}</p>
              <p className="text-sm text-slate-600 mt-1">{t("me.gdpr_body")}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <a
                  href={`mailto:Terziclaudio@gmail.com?subject=${encodeURIComponent(t("me.gdpr_export_subject"))}&body=${encodeURIComponent(t("me.gdpr_export_body"))}`}
                  className="btn-outline !py-2 !px-4 text-sm"
                  data-testid="me-gdpr-export"
                >
                  <Download className="h-4 w-4" /> {t("me.gdpr_export")}
                </a>
                <button
                  onClick={deleteMyData}
                  className="!py-2 !px-4 text-sm rounded-xl border border-red-300 text-red-600 hover:bg-red-50 inline-flex items-center gap-2 font-medium transition"
                  data-testid="me-gdpr-delete"
                >
                  <Trash2 className="h-4 w-4" /> {t("me.gdpr_delete")}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoginScreen({ showRequest, setShowRequest, emailInput, setEmailInput, sending, magicMode, requestMagicLink, googleLogin, t }) {
  return (
    <div className="section">
      <div className="container-narrow max-w-md" data-testid="me-login">
        <div className="card-clean p-8 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#5BA4D4]/10 text-[#5BA4D4]">
            <Mail className="h-7 w-7" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold text-navy">{t("me.title")}</h1>
          <p className="mt-2 text-sm text-slate-500">{t("me.login_desc")}</p>

          {!showRequest && magicMode !== "sent" && (
            <div className="mt-6 space-y-2">
              <button onClick={() => setShowRequest(true)} className="btn-primary w-full justify-center" data-testid="me-login-magic">
                <Mail className="h-4 w-4" /> {t("me.login_by_email")}
              </button>
              <button onClick={googleLogin} className="btn-outline w-full justify-center" data-testid="me-login-google">
                <LogIn className="h-4 w-4" /> {t("me.login_google")}
              </button>
            </div>
          )}

          {showRequest && magicMode !== "sent" && (
            <div className="mt-6 space-y-3 text-left" data-testid="me-magic-form">
              <label className="block text-sm">
                <span className="font-medium text-navy">{t("booking.email")}</span>
                <input
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="vous@exemple.com"
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20"
                  data-testid="me-magic-email"
                />
              </label>
              <button disabled={!emailInput || sending} onClick={requestMagicLink} className="btn-primary w-full justify-center disabled:opacity-40" data-testid="me-magic-submit">
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Mail className="h-4 w-4" />}
                {t("me.send_magic_link")}
              </button>
              <button onClick={() => setShowRequest(false)} className="text-xs text-slate-500 hover:text-navy">
                ← {t("me.back")}
              </button>
            </div>
          )}

          {magicMode === "sent" && (
            <div className="mt-6 p-4 rounded-lg bg-emerald-50 text-emerald-700 text-sm" data-testid="me-magic-sent">
              <Check className="inline h-4 w-4 mr-1" />
              {t("me.magic_check_email")} <b>{emailInput}</b>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function NoUpcomingCard({ lastRebookSource, rebookLike, t }) {
  return (
    <div className="mt-8 card-clean p-6 flex flex-wrap justify-between items-center gap-4" data-testid="me-no-upcoming">
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
          <Star className="h-6 w-6" />
        </div>
        <div>
          <p className="font-semibold text-navy">{t("me.no_upcoming_title")}</p>
          <p className="text-sm text-slate-500">{t("me.no_upcoming_sub")}</p>
        </div>
      </div>
      <button onClick={() => rebookLike(lastRebookSource)} className="btn-primary" data-testid="me-rebook-now">
        <Calendar className="h-4 w-4" /> {t("me.rebook_now")}
      </button>
    </div>
  );
}

function ContractCard({ contract: c, onRebook, onUpload, uploading, t }) {
  const [showBefore, setShowBefore] = React.useState(false);
  const [showAfter, setShowAfter] = React.useState(false);
  return (
    <div className="card-clean p-5" data-testid={`me-contract-${c.id}`}>
      <div className="flex flex-wrap justify-between items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs uppercase tracking-wider font-semibold text-slate-400">
              {t("me.ref")}: {c.id.slice(0, 8).toUpperCase()}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLOR[c.status] || "bg-slate-50 text-slate-500 border-slate-200"}`}>
              {c.status === "signed" && <Check className="inline h-3 w-3 mr-1" />}
              {t(`me.status.${c.status}`)}
            </span>
          </div>
          <p className="font-semibold text-navy">{c.service_label}</p>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
            <span className="flex items-center gap-1"><Calendar className="h-3 w-3" /> {c.date} · {c.time_slot}</span>
            <span>€{c.service_price}</span>
          </div>
          {c.dirty_area_description && (
            <p className="mt-2 text-xs text-slate-500 italic">&ldquo;{c.dirty_area_description}&rdquo;</p>
          )}
        </div>
        <a
          href={`${API}/contracts/${c.id}/pdf`}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary !py-2 !px-4 text-sm"
          data-testid={`me-pdf-${c.id}`}
        >
          <Download className="h-4 w-4" /> PDF
        </a>
      </div>

      {/* Photos row */}
      <div className="mt-4 grid grid-cols-2 gap-3" data-testid={`me-photos-${c.id}`}>
        <div>
          <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5">
            {t("me.photo_before")}
          </p>
          {c.has_photo_before ? (
            <button
              onClick={() => setShowBefore((v) => !v)}
              className="w-full aspect-video rounded-lg overflow-hidden bg-slate-100 hover:opacity-80 transition"
              data-testid={`me-photo-before-btn-${c.id}`}
            >
              <ClientAuthImg contractId={c.id} kind="before" alt="Before" />
            </button>
          ) : (
            <div className="w-full aspect-video rounded-lg bg-slate-100 flex items-center justify-center text-slate-400 text-xs italic">
              {t("me.no_photo")}
            </div>
          )}
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 mb-1.5 flex items-center gap-1">
            {t("me.photo_after")}
            {c.has_photo_after && <Check className="h-3 w-3 text-emerald-500" />}
          </p>
          {c.has_photo_after ? (
            <div className="w-full aspect-video rounded-lg overflow-hidden bg-slate-100">
              <ClientAuthImg contractId={c.id} kind="after" alt="After" />
            </div>
          ) : (
            <label className="w-full aspect-video rounded-lg border-2 border-dashed border-slate-300 hover:border-[#5BA4D4] flex flex-col items-center justify-center gap-1 text-slate-500 cursor-pointer transition" data-testid={`me-upload-after-${c.id}`}>
              {uploading ? (
                <>
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="text-xs">{t("me.uploading")}</span>
                </>
              ) : (
                <>
                  <Camera className="h-6 w-6" />
                  <span className="text-xs font-medium">{t("me.take_after_photo")}</span>
                  <span className="text-[10px]">{t("me.take_after_hint")}</span>
                </>
              )}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={(e) => onUpload(e.target.files?.[0])}
              />
            </label>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap gap-2 justify-between">
        <div className="flex items-center gap-1 text-xs text-slate-500">
          {c.has_photo_after ? (
            <><Check className="h-3 w-3 text-emerald-500" /> {t("me.after_ok")}</>
          ) : (
            <><Clock className="h-3 w-3 text-amber-500" /> {t("me.after_pending")}</>
          )}
        </div>
        <button
          onClick={onRebook}
          className="text-xs rounded-lg bg-[#5BA4D4]/10 text-[#5BA4D4] hover:bg-[#5BA4D4]/20 px-3 py-1.5 font-medium flex items-center gap-1"
          data-testid={`me-rebook-c-${c.id}`}
        >
          {t("me.rebook_same_service")} <ChevronRight className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}

function ClientAuthImg({ contractId, kind, alt }) {
  const [src, setSrc] = React.useState(null);
  React.useEffect(() => {
    let url;
    api
      .get(`/client/contracts/${contractId}/photo/${kind}`, { responseType: "blob" })
      .then((r) => {
        url = URL.createObjectURL(r.data);
        setSrc(url);
      })
      .catch(() => {});
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [contractId, kind]);
  return src ? <img src={src} alt={alt} className="w-full h-full object-cover" /> : null;
}
