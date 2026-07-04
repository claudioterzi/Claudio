import React from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { ChevronRight, ChevronLeft, Plus, Minus, Check, Sparkles, Calendar as CalendarIcon } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
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

function formatDate(d) {
  if (!d) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth()+1).padStart(2,'0');
  const day = String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}

export default function Booking() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const [step, setStep] = React.useState(1);
  const [items, setItems] = React.useState(() => {
    const pre = location.state?.preselect;
    return pre ? [{ service_id: pre, quantity: 1 }] : [];
  });

  const [form, setForm] = React.useState({
    full_name: "", phone: "", email: "", address: "", city: "Bruxelles", postal_code: "", notes: "",
  });
  const [date, setDate] = React.useState(null);
  const [timeSlot, setTimeSlot] = React.useState("");
  const [availability, setAvailability] = React.useState([]);
  const [promoCode, setPromoCode] = React.useState("");
  const [quote, setQuote] = React.useState({ subtotal: 0, travel_fee: 0, promo_discount: 0, promo_applied: "", total: 0 });
  const [submitting, setSubmitting] = React.useState(false);
  const [done, setDone] = React.useState(false);

  const subtotal = items.reduce((sum, it) => {
    const s = SERVICES.find(x => x.id === it.service_id);
    return sum + (s ? s.price * Math.max(1, it.quantity) : 0);
  }, 0);
  const total = quote.total || subtotal;

  React.useEffect(() => {
    if (date) {
      const ds = formatDate(date);
      api.get(`/availability?date=${ds}`).then(r => setAvailability(r.data.slots || [])).catch(()=>setAvailability([]));
    }
  }, [date]);

  // Recompute quote when items, postal_code or promo change
  React.useEffect(() => {
    if (items.length === 0) { setQuote({ subtotal: 0, travel_fee: 0, promo_discount: 0, promo_applied: "", total: 0 }); return; }
    const ctrl = setTimeout(() => {
      api.post("/quote", { items, postal_code: form.postal_code, promo_code: promoCode })
        .then(r => setQuote(r.data)).catch(()=>{});
    }, 250);
    return () => clearTimeout(ctrl);
  }, [items, form.postal_code, promoCode]);

  const addService = (sid) => {
    if (items.find(it => it.service_id === sid)) return;
    setItems([...items, { service_id: sid, quantity: 1 }]);
  };
  const removeService = (sid) => setItems(items.filter(it => it.service_id !== sid));
  const setQuantity = (sid, q) => setItems(items.map(it => it.service_id === sid ? { ...it, quantity: Math.max(1, q) } : it));

  const unitLabel = (u) => u === "m2" ? t("services.per_m2") : u === "marche" ? t("services.per_step") : "";

  const submit = async () => {
    setSubmitting(true);
    try {
      await api.post("/bookings", {
        items,
        ...form,
        date: formatDate(date),
        time_slot: timeSlot,
        language: i18n.language,
        promo_code: promoCode,
      });
      setDone(true);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erreur");
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="section">
        <div className="container-narrow max-w-2xl text-center" data-testid="booking-success">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#5BA4D4]/15 text-[#5BA4D4]">
            <Check className="h-8 w-8" />
          </div>
          <h2 className="mt-6 text-3xl font-semibold text-navy">{t("booking.success_title")}</h2>
          <p className="mt-3 text-slate-600">{t("booking.success_body")}</p>
          <button onClick={() => { setDone(false); setStep(1); setItems([]); setDate(null); setTimeSlot(""); }} className="btn-primary mt-8" data-testid="booking-new-cta">
            {t("booking.new_booking")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="section">
      <div className="container-narrow max-w-4xl">
        <h1 className="text-3xl sm:text-4xl font-semibold text-navy" data-testid="booking-title">{t("booking.title")}</h1>

        <div className="mt-6 flex flex-wrap gap-2 text-sm">
          {[1,2,3].map(s => (
            <div key={s} className={`flex-1 min-w-[80px] rounded-lg px-3 py-2 ${step>=s ? 'bg-[#1B2845] text-white' : 'bg-slate-100 text-slate-500'}`} data-testid={`step-indicator-${s}`}>
              {s}. {s===1?t("booking.step1"):s===2?t("booking.step2"):t("booking.step3")}
            </div>
          ))}
        </div>

        {/* STEP 1 - Services */}
        {step === 1 && (
          <div className="mt-8" data-testid="step-1-services">
            <div className="grid sm:grid-cols-2 gap-3">
              {SERVICES.map(s => {
                const selected = items.find(it => it.service_id === s.id);
                return (
                  <div key={s.id} className={`card-clean p-4 ${selected ? 'ring-2 ring-[#5BA4D4]' : ''}`} data-testid={`booking-service-${s.id}`}>
                    <div className="flex justify-between items-start gap-2">
                      <div>
                        <p className="font-semibold text-navy">{t(`services.items.${s.id}.name`)}</p>
                        <p className="text-sm text-slate-500">€{s.price} {unitLabel(s.unit)}</p>
                      </div>
                      {selected ? (
                        <button onClick={() => removeService(s.id)} className="text-sm text-red-600 font-medium" data-testid={`booking-remove-${s.id}`}>{t("booking.remove")}</button>
                      ) : (
                        <button onClick={() => addService(s.id)} className="text-sm text-[#5BA4D4] font-semibold flex items-center gap-1" data-testid={`booking-add-${s.id}`}><Plus className="h-4 w-4" />{t("booking.add_service")}</button>
                      )}
                    </div>
                    {selected && (s.unit === "m2" || s.unit === "marche") && (
                      <div className="mt-3 flex items-center gap-2">
                        <span className="text-sm text-slate-600">{t("booking.quantity")}:</span>
                        <button onClick={() => setQuantity(s.id, selected.quantity - 1)} className="h-8 w-8 rounded border border-slate-300"><Minus className="h-3 w-3 mx-auto" /></button>
                        <input type="number" min="1" value={selected.quantity} onChange={e => setQuantity(s.id, parseInt(e.target.value)||1)} className="w-16 h-8 rounded border border-slate-300 text-center" data-testid={`booking-qty-${s.id}`} />
                        <button onClick={() => setQuantity(s.id, selected.quantity + 1)} className="h-8 w-8 rounded border border-slate-300"><Plus className="h-3 w-3 mx-auto" /></button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div className="mt-6 flex items-center justify-between rounded-xl bg-soft px-5 py-4">
              <span className="text-slate-700">{t("booking.estimate")}</span>
              <span className="text-2xl font-bold text-navy" data-testid="booking-total">€{subtotal}</span>
            </div>
            <div className="mt-6 flex justify-end">
              <button disabled={items.length === 0} onClick={() => setStep(2)} className="btn-primary disabled:opacity-40" data-testid="booking-next-1">
                {t("booking.next")} <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2 - Contact */}
        {step === 2 && (
          <div className="mt-8 grid sm:grid-cols-2 gap-4" data-testid="step-2-contact">
            <Field label={t("booking.full_name")} value={form.full_name} onChange={v=>setForm({...form, full_name:v})} testid="booking-full-name" required />
            <Field label={t("booking.phone")} value={form.phone} onChange={v=>setForm({...form, phone:v})} testid="booking-phone" required />
            <Field label={t("booking.email")} type="email" value={form.email} onChange={v=>setForm({...form, email:v})} testid="booking-email" required />
            <Field label={t("booking.postal_code")} value={form.postal_code} onChange={v=>setForm({...form, postal_code:v})} testid="booking-postal" required />
            <Field className="sm:col-span-2" label={t("booking.address")} value={form.address} onChange={v=>setForm({...form, address:v})} testid="booking-address" required />
            <Field label={t("booking.city")} value={form.city} onChange={v=>setForm({...form, city:v})} testid="booking-city" required />
            <Field className="sm:col-span-2" label={t("booking.notes")} value={form.notes} onChange={v=>setForm({...form, notes:v})} testid="booking-notes" textarea />
            <div className="sm:col-span-2 flex justify-between mt-2">
              <button onClick={() => setStep(1)} className="btn-outline" data-testid="booking-back-2"><ChevronLeft className="h-4 w-4" />{t("booking.back")}</button>
              <button disabled={!form.full_name || !form.phone || !form.email || !form.address || !form.postal_code} onClick={() => setStep(3)} className="btn-primary disabled:opacity-40" data-testid="booking-next-2">{t("booking.next")}<ChevronRight className="h-4 w-4" /></button>
            </div>
          </div>
        )}

        {/* STEP 3 - Date & time */}
        {step === 3 && (
          <div className="mt-8 grid lg:grid-cols-2 gap-8" data-testid="step-3-datetime">
            <div>
              <p className="text-sm font-semibold text-navy mb-2 flex items-center gap-2"><CalendarIcon className="h-4 w-4 text-[#5BA4D4]" /> {t("booking.date")}</p>
              <div className="rounded-xl border border-slate-200 p-2 inline-block">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  disabled={(d) => d < new Date(new Date().toDateString())}
                  data-testid="booking-calendar"
                />
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold text-navy mb-2">{t("booking.time_slot")}</p>
              <div className="grid gap-2">
                {availability.length === 0 && date && <p className="text-sm text-slate-500">…</p>}
                {availability.map(s => (
                  <button
                    key={s.slot}
                    disabled={!s.available}
                    onClick={() => setTimeSlot(s.slot)}
                    className={`rounded-xl border px-4 py-3 text-left transition ${
                      timeSlot === s.slot ? 'border-[#5BA4D4] bg-[#5BA4D4]/10 text-navy' :
                      s.available ? 'border-slate-200 hover:border-[#5BA4D4]' : 'border-slate-100 bg-slate-50 text-slate-400 cursor-not-allowed'
                    }`}
                    data-testid={`booking-slot-${s.slot}`}
                  >
                    <span className="font-medium">{s.slot}</span>
                    {!s.available && <span className="ml-2 text-xs">· {t("booking.unavailable")}</span>}
                  </button>
                ))}
                {!date && <p className="text-sm text-slate-500">→ {t("booking.date")}</p>}
              </div>

              <div className="mt-8 rounded-xl bg-soft p-5 space-y-2 text-sm">
                <div className="flex justify-between"><span>Sous-total</span><span className="font-medium">€{quote.subtotal || subtotal}</span></div>
                {quote.travel_fee > 0 && <div className="flex justify-between text-slate-600"><span>Frais déplacement</span><span>+€{quote.travel_fee}</span></div>}
                {quote.travel_fee === 0 && items.length > 0 && form.postal_code && <div className="flex justify-between text-emerald-600"><span>Frais déplacement</span><span>Gratuit</span></div>}
                <div className="pt-2">
                  <label className="flex gap-2 items-center text-xs text-slate-600">Code promo
                    <input value={promoCode} onChange={e=>setPromoCode(e.target.value.toUpperCase())} placeholder="VOISIN20" className="ml-auto w-32 rounded border border-slate-200 px-2 py-1 text-xs uppercase" data-testid="booking-promo-input" />
                  </label>
                  {quote.promo_applied && <p className="text-xs text-emerald-600 mt-1">✓ {quote.promo_applied} appliqué : −€{quote.promo_discount}</p>}
                </div>
                <div className="flex justify-between border-t pt-2 text-base">
                  <span className="font-semibold">{t("booking.estimate")}</span>
                  <span className="text-xl font-bold text-navy">€{quote.total || subtotal}</span>
                </div>
              </div>

              <div className="mt-6 flex justify-between">
                <button onClick={() => setStep(2)} className="btn-outline" data-testid="booking-back-3"><ChevronLeft className="h-4 w-4" />{t("booking.back")}</button>
                <button disabled={!date || !timeSlot || submitting} onClick={submit} className="btn-primary disabled:opacity-40" data-testid="booking-submit">
                  {submitting ? "…" : t("booking.submit")}
                  <Check className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type="text", required, className="", testid, textarea=false }) {
  const props = {
    value, onChange: e => onChange(e.target.value), required,
    "data-testid": testid,
    className: "mt-1 w-full rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm focus:border-[#5BA4D4] focus:outline-none focus:ring-2 focus:ring-[#5BA4D4]/20",
  };
  return (
    <label className={`block text-sm text-slate-700 ${className}`}>
      <span className="font-medium">{label}{required && " *"}</span>
      {textarea ? <textarea rows={3} {...props} /> : <input type={type} {...props} />}
    </label>
  );
}
