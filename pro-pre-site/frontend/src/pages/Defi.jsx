import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Calendar } from "@/components/ui/calendar";
import {
  Sparkles,
  Calendar as CalendarIcon,
  Check,
  ChevronRight,
  ChevronLeft,
  Camera,
  Upload,
  FileText,
  ShieldCheck,
  CreditCard,
  Wallet,
  User as UserIcon,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

const SERVICES = [
  { id: "canape_2", price: 80, unit: "fixe" },
  { id: "canape_3", price: 110, unit: "fixe" },
  { id: "canape_ang", price: 150, unit: "fixe" },
  { id: "matelas_1", price: 65, unit: "fixe" },
  { id: "matelas_2", price: 90, unit: "fixe" },
  { id: "tapis", price: 20, unit: "m2" },
  { id: "escaliers", price: 7, unit: "marche" },
  { id: "auto", price: 100, unit: "fixe" },
];

const DEPOSIT_OPTIONS = [
  { id: "none", icon: Wallet, color: "text-slate-500" },
  { id: "stripe", icon: CreditCard, color: "text-[#5BA4D4]" },
  { id: "bonifico", icon: FileText, color: "text-emerald-600" },
  { id: "in_person", icon: Wallet, color: "text-amber-600" },
];

function formatDate(d) {
  if (!d) return "";
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

async function resizeImage(file, maxDim = 1400, quality = 0.82) {
  const dataUrl = await fileToBase64(file);
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

export default function Defi() {
  const { t, i18n } = useTranslation();
  const [step, setStep] = React.useState(1);
  const [form, setForm] = React.useState({
    full_name: "",
    phone: "",
    email: "",
    address: "",
    city: "Bruxelles",
    postal_code: "",
    notes: "",
    service_id: "",
    quantity: 1,
    dirty_area_description: "",
    photo_before_base64: "",
    signature_typed: "",
    deposit_choice: "none",
  });
  const [date, setDate] = React.useState(null);
  const [timeSlot, setTimeSlot] = React.useState("");
  const [availability, setAvailability] = React.useState([]);
  const [acceptTerms, setAcceptTerms] = React.useState(false);
  const [galleryConsent, setGalleryConsent] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [done, setDone] = React.useState(null); // response from server
  const [photoPreview, setPhotoPreview] = React.useState("");

  React.useEffect(() => {
    if (date) {
      api
        .get(`/availability?date=${formatDate(date)}`)
        .then((r) => setAvailability(r.data.slots || []))
        .catch(() => setAvailability([]));
    }
  }, [date]);

  const set = (patch) => setForm((f) => ({ ...f, ...patch }));

  const handlePhoto = async (file) => {
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) {
      toast.error(t("defi_flow.photo_too_big"));
      return;
    }
    try {
      const b64 = await resizeImage(file);
      set({ photo_before_base64: b64 });
      setPhotoPreview(b64);
    } catch {
      toast.error(t("defi_flow.photo_error"));
    }
  };

  const svc = SERVICES.find((s) => s.id === form.service_id);
  const price = svc ? svc.price * Math.max(1, form.quantity) : 0;

  const step1Valid =
    form.full_name && form.phone && form.email && form.address && form.postal_code && date && timeSlot;
  const step2Valid = form.service_id && form.dirty_area_description && form.photo_before_base64;
  const step3Valid = form.signature_typed.trim() && acceptTerms;

  const submit = async () => {
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        // Stripe is handled server-side after contract creation. We still register the choice.
        deposit_choice: form.deposit_choice === "stripe" ? "stripe" : form.deposit_choice,
        date: formatDate(date),
        time_slot: timeSlot,
        language: i18n.language,
        accept_terms: acceptTerms,
        gallery_consent: galleryConsent,
      };
      const r = await api.post("/contracts", payload);
      // If user chose Stripe → create checkout session and redirect
      if (form.deposit_choice === "stripe") {
        try {
          const chk = await api.post("/checkout/session", {
            package_id: "defi_deposit_30",
            origin_url: window.location.origin,
            contract_id: r.data.contract_id,
            metadata: { client_email: form.email, language: i18n.language },
          });
          if (chk.data?.url) {
            window.location.href = chk.data.url;
            return;
          }
        } catch (e) {
          toast.error(t("defi_flow.stripe_error"));
        }
      }
      setDone(r.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || t("defi_flow.submit_error"));
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="section">
        <div className="container-narrow max-w-2xl text-center" data-testid="defi-success">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
            <Check className="h-8 w-8" />
          </div>
          <h2 className="mt-6 text-3xl font-semibold text-navy">{t("defi_flow.success_title")}</h2>
          <p className="mt-3 text-slate-600">{t("defi_flow.success_body")}</p>
          <div className="mt-6 space-y-3">
            <a
              href={done.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary justify-center"
              data-testid="defi-pdf-link"
            >
              <FileText className="h-4 w-4" /> {t("defi_flow.download_pdf")}
            </a>
            <p className="text-sm text-slate-500">
              {t("defi_flow.magic_sent")} <b>{form.email}</b>
            </p>
          </div>
          {form.deposit_choice === "bonifico" && (
            <div className="mt-8 card-clean p-5 text-left">
              <h3 className="font-semibold text-navy">{t("defi_flow.iban_title")}</h3>
              <p className="text-sm text-slate-600 mt-2">
                {t("defi_flow.iban_beneficiary")}: <b>Claudio Terzi — Pro-pre</b>
                <br />
                IBAN: <b className="tracking-wider">BE00 0000 0000 0000</b>
                <br />
                BIC: <b>GEBABEBB</b>
                <br />
                {t("defi_flow.iban_ref")}: <b>{done.contract_id.slice(0, 8).toUpperCase()}</b>
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="section">
      <div className="container-narrow max-w-4xl">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#5BA4D4] text-white">
            <Sparkles className="h-6 w-6" />
          </div>
          <p className="eyebrow">{t("defi.kicker")}</p>
        </div>
        <h1 className="text-3xl sm:text-4xl font-semibold text-navy" data-testid="defi-title">
          {t("defi_flow.title")}
        </h1>
        <p className="mt-2 text-slate-600">{t("defi_flow.subtitle")}</p>

        {/* Progress */}
        <div className="mt-8 flex items-center gap-2" data-testid="defi-progress">
          {[1, 2, 3].map((n) => (
            <React.Fragment key={n}>
              <div
                className={`h-9 w-9 rounded-full flex items-center justify-center text-sm font-semibold border-2 transition ${
                  step === n
                    ? "border-[#5BA4D4] bg-[#5BA4D4] text-white"
                    : step > n
                      ? "border-emerald-500 bg-emerald-500 text-white"
                      : "border-slate-300 bg-white text-slate-400"
                }`}
              >
                {step > n ? <Check className="h-4 w-4" /> : n}
              </div>
              {n < 3 && (
                <div className={`flex-1 h-0.5 ${step > n ? "bg-emerald-500" : "bg-slate-200"}`} />
              )}
            </React.Fragment>
          ))}
        </div>
        <div className="mt-2 flex justify-between text-xs text-slate-500">
          <span>{t("defi_flow.step1_label")}</span>
          <span>{t("defi_flow.step2_label")}</span>
          <span>{t("defi_flow.step3_label")}</span>
        </div>

        {/* STEP 1 — Client info + Address + Date */}
        {step === 1 && (
          <div className="mt-8 grid lg:grid-cols-2 gap-8" data-testid="defi-step1">
            <div className="grid gap-4">
              <Field
                label={t("booking.full_name")}
                value={form.full_name}
                onChange={(v) => set({ full_name: v })}
                testid="defi-name"
                icon={<UserIcon className="h-4 w-4" />}
              />
              <Field
                label={t("booking.phone")}
                value={form.phone}
                onChange={(v) => set({ phone: v })}
                testid="defi-phone"
              />
              <Field
                label={t("booking.email")}
                type="email"
                value={form.email}
                onChange={(v) => set({ email: v })}
                testid="defi-email"
              />
              <Field
                label={t("booking.address")}
                value={form.address}
                onChange={(v) => set({ address: v })}
                testid="defi-address"
              />
              <div className="grid grid-cols-2 gap-3">
                <Field
                  label={t("booking.postal_code")}
                  value={form.postal_code}
                  onChange={(v) => set({ postal_code: v })}
                  testid="defi-postal"
                />
                <Field
                  label={t("booking.city")}
                  value={form.city}
                  onChange={(v) => set({ city: v })}
                  testid="defi-city"
                />
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold text-navy mb-2 flex items-center gap-2">
                <CalendarIcon className="h-4 w-4 text-[#5BA4D4]" />
                {t("booking.date")}
              </p>
              <div className="rounded-xl border border-slate-200 p-2 inline-block">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  disabled={(d) => d < new Date(new Date().toDateString())}
                  data-testid="defi-calendar"
                />
              </div>
              <p className="text-sm font-semibold text-navy mt-6 mb-2">{t("booking.time_slot")}</p>
              <div className="grid gap-2">
                {availability.map((s) => (
                  <button
                    key={s.slot}
                    disabled={!s.available}
                    onClick={() => setTimeSlot(s.slot)}
                    className={`rounded-xl border px-4 py-3 text-left ${
                      timeSlot === s.slot
                        ? "border-[#5BA4D4] bg-[#5BA4D4]/10"
                        : s.available
                          ? "border-slate-200 hover:border-[#5BA4D4]"
                          : "border-slate-100 bg-slate-50 text-slate-400 cursor-not-allowed"
                    }`}
                    data-testid={`defi-slot-${s.slot}`}
                  >
                    {s.slot}
                    {!s.available && <span className="text-xs ml-2">· {t("booking.unavailable")}</span>}
                  </button>
                ))}
                {!date && <p className="text-sm text-slate-500">→ {t("booking.date")}</p>}
              </div>
            </div>
          </div>
        )}

        {/* STEP 2 — Service + Photo + Dirty area */}
        {step === 2 && (
          <div className="mt-8 grid lg:grid-cols-2 gap-8" data-testid="defi-step2">
            <div>
              <p className="text-sm font-semibold text-navy mb-3">{t("defi_flow.choose_service")}</p>
              <div className="grid gap-2" data-testid="defi-service-list">
                {SERVICES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => set({ service_id: s.id, quantity: 1 })}
                    className={`rounded-xl border px-4 py-3 text-left transition ${
                      form.service_id === s.id
                        ? "border-[#5BA4D4] bg-[#5BA4D4]/10"
                        : "border-slate-200 hover:border-[#5BA4D4]"
                    }`}
                    data-testid={`defi-svc-${s.id}`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-navy">{t(`services.items.${s.id}.name`)}</p>
                        <p className="text-xs text-slate-500">
                          €{s.price}
                          {s.unit === "m2" ? "/m²" : s.unit === "marche" ? "/" + t("defi_flow.step") : ""}
                        </p>
                      </div>
                      {form.service_id === s.id && <Check className="h-5 w-5 text-[#5BA4D4]" />}
                    </div>
                  </button>
                ))}
              </div>
              {svc && (svc.unit === "m2" || svc.unit === "marche") && (
                <div className="mt-4">
                  <Field
                    type="number"
                    label={
                      svc.unit === "m2"
                        ? t("defi_flow.area_m2")
                        : t("defi_flow.stairs_count")
                    }
                    value={form.quantity}
                    onChange={(v) => set({ quantity: Math.max(1, parseFloat(v) || 1) })}
                    testid="defi-quantity"
                  />
                </div>
              )}
              {svc && (
                <div className="mt-4 p-3 rounded-lg bg-emerald-50 text-emerald-700 text-sm" data-testid="defi-price-preview">
                  {t("defi_flow.price_preview")}: <b>€{price}</b>
                  <br />
                  <span className="text-xs">{t("defi_flow.price_note")}</span>
                </div>
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-navy mb-2 flex items-center gap-2">
                <Camera className="h-4 w-4 text-[#5BA4D4]" />
                {t("defi_flow.photo_label")}
              </p>
              <label
                className="block cursor-pointer rounded-xl border-2 border-dashed border-slate-300 hover:border-[#5BA4D4] p-6 text-center"
                data-testid="defi-photo-upload"
              >
                {photoPreview ? (
                  <img src={photoPreview} alt="dirty product" className="max-h-56 mx-auto rounded-lg" />
                ) : (
                  <div className="flex flex-col items-center gap-2 text-slate-500">
                    <Upload className="h-8 w-8" />
                    <span className="text-sm">{t("defi_flow.photo_cta")}</span>
                    <span className="text-xs">{t("defi_flow.photo_hint")}</span>
                  </div>
                )}
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={(e) => handlePhoto(e.target.files?.[0])}
                />
              </label>
              <div className="mt-4">
                <label className="block text-sm font-medium text-navy">
                  {t("defi_flow.dirty_area_label")} *
                </label>
                <textarea
                  rows={3}
                  value={form.dirty_area_description}
                  onChange={(e) => set({ dirty_area_description: e.target.value })}
                  placeholder={t("defi_flow.dirty_area_placeholder")}
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20"
                  data-testid="defi-dirty-area"
                />
              </div>
              <div className="mt-4">
                <label className="block text-sm font-medium text-navy">{t("booking.notes")}</label>
                <textarea
                  rows={2}
                  value={form.notes}
                  onChange={(e) => set({ notes: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20"
                  data-testid="defi-notes"
                />
              </div>
            </div>
          </div>
        )}

        {/* STEP 3 — Deposit + Signature + Terms */}
        {step === 3 && (
          <div className="mt-8 grid lg:grid-cols-2 gap-8" data-testid="defi-step3">
            <div>
              <p className="text-sm font-semibold text-navy mb-3">
                {t("defi_flow.deposit_title")}
              </p>
              <p className="text-xs text-slate-500 mb-3">{t("defi_flow.deposit_desc")}</p>
              <div className="grid gap-2">
                {DEPOSIT_OPTIONS.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => set({ deposit_choice: d.id })}
                    className={`rounded-xl border px-4 py-3 text-left transition flex items-center gap-3 ${
                      form.deposit_choice === d.id
                        ? "border-[#5BA4D4] bg-[#5BA4D4]/10"
                        : "border-slate-200 hover:border-[#5BA4D4]"
                    }`}
                    data-testid={`defi-deposit-${d.id}`}
                  >
                    <d.icon className={`h-5 w-5 ${d.color}`} />
                    <div className="flex-1">
                      <p className="font-medium text-navy text-sm">{t(`defi_flow.deposit_${d.id}_title`)}</p>
                      <p className="text-xs text-slate-500">{t(`defi_flow.deposit_${d.id}_desc`)}</p>
                    </div>
                    {form.deposit_choice === d.id && <Check className="h-5 w-5 text-[#5BA4D4]" />}
                  </button>
                ))}
              </div>
              {form.deposit_choice === "stripe" && (
                <div className="mt-3 p-3 rounded-lg bg-[#5BA4D4]/10 text-[#1B2845] text-xs" data-testid="stripe-notice">
                  🔒 {t("defi_flow.stripe_notice")}
                </div>
              )}
            </div>
            <div>
              <p className="text-sm font-semibold text-navy mb-3 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                {t("defi_flow.contract_review")}
              </p>
              <div className="card-clean p-4 text-sm text-slate-600 mb-4 max-h-40 overflow-y-auto" data-testid="defi-contract-preview">
                <p><b>{t("defi_flow.your_appointment")}:</b> {formatDate(date)} · {timeSlot}</p>
                <p><b>{t("booking.address")}:</b> {form.address}, {form.postal_code} {form.city}</p>
                <p><b>{t("defi_flow.related_service")}:</b> {svc ? t(`services.items.${svc.id}.name`) : "—"} · €{price}</p>
                <p><b>{t("defi_flow.dirty_area_label")}:</b> {form.dirty_area_description}</p>
                <p className="mt-3 font-medium text-navy">{t("defi_flow.guarantees_title")}:</p>
                <ul className="list-disc list-inside text-xs mt-1 space-y-1">
                  <li>{t("defi_flow.guarantee_1")}</li>
                  <li>{t("defi_flow.guarantee_2")}</li>
                  <li>{t("defi_flow.guarantee_3")}</li>
                </ul>
              </div>

              <label className="block text-sm font-medium text-navy">
                {t("defi_flow.signature_label")} *
              </label>
              <input
                value={form.signature_typed}
                onChange={(e) => set({ signature_typed: e.target.value })}
                placeholder={t("defi_flow.signature_placeholder")}
                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20"
                data-testid="defi-signature-input"
              />
              {form.signature_typed && (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <div className="rounded-lg border border-slate-200 p-4 text-center bg-white">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">
                      {t("defi_flow.client_signature")}
                    </p>
                    <p
                      className="text-2xl text-navy italic"
                      style={{ fontFamily: "'Brush Script MT', 'Lucida Handwriting', cursive" }}
                      data-testid="defi-signature-preview"
                    >
                      {form.signature_typed}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-200 p-4 text-center bg-slate-50">
                    <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">
                      {t("defi_flow.prestataire_signature")}
                    </p>
                    <p
                      className="text-2xl text-navy italic font-bold"
                      style={{ fontFamily: "'Brush Script MT', 'Lucida Handwriting', cursive" }}
                    >
                      Claudio Terzi
                    </p>
                  </div>
                </div>
              )}

              <label className="mt-4 flex items-start gap-3 cursor-pointer" data-testid="defi-terms-label">
                <input
                  type="checkbox"
                  checked={acceptTerms}
                  onChange={(e) => setAcceptTerms(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-[#5BA4D4] focus:ring-[#5BA4D4]"
                  data-testid="defi-terms-checkbox"
                />
                <span className="text-sm text-slate-600">
                  {(() => {
                    const raw = t("defi_flow.terms_accept");
                    // Two placeholders: [CGV link] and [Privacy link]
                    const parts = raw.split(/\[([^\]]+)\]/);
                    return parts.map((chunk, i) => {
                      if (i % 2 === 0) return <React.Fragment key={`t-${i}`}>{chunk}</React.Fragment>;
                      // First bracket → CGV, second → Privacy
                      const isFirst = i === 1;
                      return (
                        <Link
                          key={`l-${i}`}
                          to={isFirst ? "/cgv" : "/privacy"}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#5BA4D4] underline font-medium"
                          data-testid={isFirst ? "defi-link-cgv" : "defi-link-privacy"}
                        >
                          {chunk}
                        </Link>
                      );
                    });
                  })()}
                </span>
              </label>

              <label className="mt-3 flex items-start gap-3 cursor-pointer" data-testid="defi-gallery-label">
                <input
                  type="checkbox"
                  checked={galleryConsent}
                  onChange={(e) => setGalleryConsent(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-[#5BA4D4] focus:ring-[#5BA4D4]"
                  data-testid="defi-gallery-checkbox"
                />
                <span className="text-sm text-slate-500">
                  {t("defi_flow.terms_accept_gallery")}
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Navigation buttons */}
        <div className="mt-10 flex justify-between gap-3">
          {step > 1 ? (
            <button
              onClick={() => setStep(step - 1)}
              className="btn-outline"
              data-testid="defi-btn-prev"
            >
              <ChevronLeft className="h-4 w-4" /> {t("defi_flow.previous")}
            </button>
          ) : (
            <div />
          )}
          {step < 3 && (
            <button
              disabled={(step === 1 && !step1Valid) || (step === 2 && !step2Valid)}
              onClick={() => setStep(step + 1)}
              className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed"
              data-testid="defi-btn-next"
            >
              {t("defi_flow.next")} <ChevronRight className="h-4 w-4" />
            </button>
          )}
          {step === 3 && (
            <button
              disabled={!step3Valid || submitting}
              onClick={submit}
              className="btn-secondary disabled:opacity-40 disabled:cursor-not-allowed"
              data-testid="defi-btn-submit"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> {t("defi_flow.signing")}
                </>
              ) : (
                <>
                  {t("defi_flow.sign_and_send")} <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", testid, icon }) {
  const cls =
    "mt-1 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20";
  return (
    <label className="block text-sm text-slate-700">
      <span className="font-medium flex items-center gap-1">
        {icon} {label} *
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cls}
        data-testid={testid}
      />
    </label>
  );
}
