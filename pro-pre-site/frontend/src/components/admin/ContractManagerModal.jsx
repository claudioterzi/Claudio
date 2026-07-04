import React from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { api } from "@/lib/api";
import {
  X,
  Save,
  Phone,
  MessageCircle,
  Mail,
  Trash2,
  Send,
  RotateCcw,
  KeyRound,
  Loader2,
  Clock,
  Ban,
  Edit3,
  History,
  Zap,
} from "lucide-react";

/**
 * Full-featured modal to manage a single contract: edit, contact, history, actions.
 * Props:
 *   - contract: current contract object (must have id, client_email, client_phone, ...)
 *   - onClose():
 *   - onChanged(): called after any successful mutation, parent should reload().
 */
const TABS = ["edit", "contact", "history", "actions"];

export default function ContractManagerModal({ contract, onClose, onChanged }) {
  const { t } = useTranslation();
  const [tab, setTab] = React.useState("edit");
  const c = contract || {};

  if (!contract) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/55 backdrop-blur-sm flex items-center justify-center p-3"
      data-testid="contract-manager-modal"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[92vh] overflow-hidden flex flex-col"
      >
        <header className="p-4 border-b border-slate-200 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{c.service_label}</p>
            <p className="font-semibold text-navy truncate">
              {c.client_name} — €{c.service_price}
            </p>
            <p className="text-xs text-slate-500 truncate">
              {c.date} · {c.time_slot} · {c.client_email}
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 flex-shrink-0" data-testid="cmm-close">
            <X className="h-4 w-4" />
          </button>
        </header>

        <nav className="flex border-b border-slate-200 bg-slate-50 text-sm">
          {TABS.map((k) => {
            const Icon = { edit: Edit3, contact: MessageCircle, history: History, actions: Zap }[k];
            return (
              <button
                key={k}
                onClick={() => setTab(k)}
                data-testid={`cmm-tab-${k}`}
                className={`flex-1 py-3 px-2 flex items-center justify-center gap-1.5 font-medium transition border-b-2 ${
                  tab === k
                    ? "border-[#5BA4D4] text-navy bg-white"
                    : "border-transparent text-slate-500 hover:text-navy"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{t(`admin.tools.tabs.${k}`)}</span>
              </button>
            );
          })}
        </nav>

        <div className="p-5 overflow-y-auto flex-1">
          {tab === "edit" && <EditTab contract={c} onChanged={onChanged} />}
          {tab === "contact" && <ContactTab contract={c} onChanged={onChanged} />}
          {tab === "history" && <HistoryTab contract={c} />}
          {tab === "actions" && <ActionsTab contract={c} onChanged={onChanged} onClose={onClose} />}
        </div>
      </div>
    </div>
  );
}

// ==================== EDIT ====================
function EditField({ k, type, full, textarea, form, set, t }) {
  return (
    <div className={full ? "sm:col-span-2" : ""}>
      <label className="text-xs font-medium text-slate-600 block mb-1">
        {t(`admin.tools.edit.${k}`)}
      </label>
      {textarea ? (
        <textarea
          value={form[k]}
          onChange={(e) => set(k, e.target.value)}
          rows={3}
          data-testid={`cmm-field-${k}`}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-[#5BA4D4]/40 focus:border-[#5BA4D4] outline-none"
        />
      ) : (
        <input
          value={form[k]}
          type={type || "text"}
          onChange={(e) => set(k, e.target.value)}
          data-testid={`cmm-field-${k}`}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:ring-2 focus:ring-[#5BA4D4]/40 focus:border-[#5BA4D4] outline-none"
        />
      )}
    </div>
  );
}

function EditTab({ contract, onChanged }) {
  const { t } = useTranslation();
  const [form, setForm] = React.useState({
    date: contract.date || "",
    time_slot: contract.time_slot || "",
    service_label: contract.service_label || "",
    service_price: contract.service_price || 0,
    client_name: contract.client_name || "",
    client_phone: contract.client_phone || "",
    client_email: contract.client_email || "",
    client_address: contract.client_address || "",
    admin_notes: contract.admin_notes || "",
  });
  const [saving, setSaving] = React.useState(false);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const save = async () => {
    setSaving(true);
    try {
      await api.patch(`/admin/contracts/${contract.id}`, {
        ...form,
        service_price: Number(form.service_price) || 0,
      });
      toast.success(t("admin.tools.edit.saved"));
      onChanged?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div data-testid="cmm-edit">
      <h4 className="font-semibold text-navy mb-3">{t("admin.tools.edit.title")}</h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <EditField k="date" type="date" form={form} set={set} t={t} />
        <EditField k="time_slot" form={form} set={set} t={t} />
        <EditField k="service_label" full form={form} set={set} t={t} />
        <EditField k="service_price" type="number" form={form} set={set} t={t} />
        <EditField k="client_name" form={form} set={set} t={t} />
        <EditField k="client_phone" form={form} set={set} t={t} />
        <EditField k="client_email" type="email" full form={form} set={set} t={t} />
        <EditField k="client_address" full form={form} set={set} t={t} />
        <EditField k="admin_notes" full textarea form={form} set={set} t={t} />
      </div>
      <button
        onClick={save}
        disabled={saving}
        className="btn-primary mt-5 w-full sm:w-auto disabled:opacity-50"
        data-testid="cmm-save"
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        {t("admin.tools.edit.save")}
      </button>
    </div>
  );
}

// ==================== CONTACT ====================
function ContactTab({ contract, onChanged }) {
  const { t } = useTranslation();
  const [emailTemplate, setEmailTemplate] = React.useState("confirm");
  const [customSubject, setCustomSubject] = React.useState("");
  const [customBody, setCustomBody] = React.useState("");
  const [sending, setSending] = React.useState(false);

  const phone = (contract.client_phone || "").replace(/[^\d]/g, "");
  const wa_confirm = t("admin.tools.contact.wa_confirm", {
    name: contract.client_name || "",
    date: contract.date || "",
    time: contract.time_slot || "",
  });
  const wa_reminder = t("admin.tools.contact.wa_reminder", {
    name: contract.client_name || "",
    time: contract.time_slot || "",
  });
  const wa_reschedule = t("admin.tools.contact.wa_reschedule", {
    name: contract.client_name || "",
    date: contract.date || "",
  });

  const waLinks = [
    { label: t("admin.tools.contact.tpl_confirm"), text: wa_confirm },
    { label: t("admin.tools.contact.tpl_reminder"), text: wa_reminder },
    { label: t("admin.tools.contact.tpl_reschedule"), text: wa_reschedule },
  ];

  const sendEmail = async () => {
    setSending(true);
    try {
      const payload = { template: emailTemplate };
      if (emailTemplate === "custom") {
        payload.subject = customSubject;
        payload.body = customBody;
      }
      await api.post(`/admin/contracts/${contract.id}/send-email`, payload);
      toast.success(t("admin.tools.contact.email_sent"));
      onChanged?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error");
    } finally {
      setSending(false);
    }
  };

  const templates = ["confirm", "reminder", "reschedule", "test_done", "thank_you", "custom"];

  return (
    <div data-testid="cmm-contact" className="space-y-6">
      {/* Direct action bar */}
      <div className="flex flex-wrap gap-2">
        <a
          href={`tel:${contract.client_phone}`}
          className="btn-outline !py-2"
          data-testid="cmm-call"
        >
          <Phone className="h-4 w-4" /> {t("admin.tools.contact.call")}
        </a>
        <a
          href={`mailto:${contract.client_email}`}
          className="btn-outline !py-2"
          data-testid="cmm-mailto"
        >
          <Mail className="h-4 w-4" /> {t("admin.tools.contact.email")}
        </a>
      </div>

      {/* WhatsApp templates */}
      <div>
        <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
          {t("admin.tools.contact.wa_templates")}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {waLinks.map((w, i) => (
            <a
              key={i}
              href={`https://wa.me/${phone}?text=${encodeURIComponent(w.text)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 p-3 text-left transition"
              data-testid={`cmm-wa-${i}`}
            >
              <div className="flex items-center gap-2 text-emerald-700 font-medium text-sm">
                <MessageCircle className="h-4 w-4" /> {w.label}
              </div>
              <p className="text-xs text-slate-600 mt-1 line-clamp-2">{w.text}</p>
            </a>
          ))}
        </div>
      </div>

      {/* Email templates */}
      <div>
        <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
          {t("admin.tools.contact.email_templates")}
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-3">
          {templates.map((k) => (
            <button
              key={k}
              onClick={() => setEmailTemplate(k)}
              data-testid={`cmm-email-tpl-${k}`}
              className={`p-2 rounded-lg text-xs font-medium border transition ${
                emailTemplate === k
                  ? "bg-[#5BA4D4]/10 border-[#5BA4D4] text-navy"
                  : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
              }`}
            >
              {t(`admin.tools.contact.tpl_${k}`)}
            </button>
          ))}
        </div>
        {emailTemplate === "custom" && (
          <div className="space-y-2">
            <input
              value={customSubject}
              onChange={(e) => setCustomSubject(e.target.value)}
              placeholder={t("admin.tools.contact.custom_subject")}
              data-testid="cmm-custom-subject"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <textarea
              value={customBody}
              onChange={(e) => setCustomBody(e.target.value)}
              rows={4}
              placeholder={t("admin.tools.contact.custom_body")}
              data-testid="cmm-custom-body"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
        )}
        <button
          onClick={sendEmail}
          disabled={sending}
          className="btn-primary mt-3 disabled:opacity-50"
          data-testid="cmm-send-email"
        >
          {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          {t("admin.tools.contact.send_email")}
        </button>
      </div>

      {/* Log a manual contact */}
      <LogContactForm contract={contract} onChanged={onChanged} />
    </div>
  );
}

function LogContactForm({ contract, onChanged }) {
  const { t } = useTranslation();
  const [channel, setChannel] = React.useState("phone");
  const [outcome, setOutcome] = React.useState("reached");
  const [note, setNote] = React.useState("");
  const [saving, setSaving] = React.useState(false);

  const submit = async () => {
    setSaving(true);
    try {
      await api.post(`/admin/contracts/${contract.id}/log-contact`, {
        channel,
        outcome,
        note,
      });
      toast.success(t("admin.tools.actions.done"));
      setNote("");
      onChanged?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border-t border-slate-200 pt-5">
      <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">
        {t("admin.tools.contact.log_contact_title")}
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-2">
        <select
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          data-testid="cmm-log-channel"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {["phone", "whatsapp", "email", "sms", "in_person", "other"].map((c) => (
            <option key={c} value={c}>
              {t(`admin.tools.contact.channel_${c}`)}
            </option>
          ))}
        </select>
        <select
          value={outcome}
          onChange={(e) => setOutcome(e.target.value)}
          data-testid="cmm-log-outcome"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          {["reached", "no_answer", "voicemail", "confirmed", "cancelled", "other"].map((c) => (
            <option key={c} value={c}>
              {t(`admin.tools.contact.outcome_${c}`)}
            </option>
          ))}
        </select>
      </div>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder={t("admin.tools.contact.note")}
        rows={2}
        data-testid="cmm-log-note"
        className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
      />
      <button
        onClick={submit}
        disabled={saving}
        className="btn-outline mt-2 !py-2 disabled:opacity-50"
        data-testid="cmm-log-save"
      >
        {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
        {t("admin.tools.contact.log_save")}
      </button>
    </div>
  );
}

// ==================== HISTORY ====================
function HistoryTab({ contract }) {
  const { t } = useTranslation();
  const log = contract.contact_log || [];
  return (
    <div data-testid="cmm-history">
      <h4 className="font-semibold text-navy mb-3">{t("admin.tools.history.title")}</h4>
      {log.length === 0 ? (
        <p className="text-sm text-slate-500 italic py-6 text-center">
          {t("admin.tools.history.empty")}
        </p>
      ) : (
        <ol className="relative border-l-2 border-slate-200 ml-2 space-y-3">
          {[...log].reverse().map((e, i) => (
            <li key={i} className="ml-4">
              <span className="absolute -left-[7px] w-3 h-3 rounded-full bg-[#5BA4D4] border-2 border-white" />
              <p className="text-xs text-slate-500 flex items-center gap-1">
                <Clock className="h-3 w-3" /> {new Date(e.at).toLocaleString()}
              </p>
              <p className="text-sm text-navy font-medium mt-0.5">
                {t(`admin.tools.contact.channel_${e.channel}`, e.channel)} ·{" "}
                <span className="text-slate-500 font-normal">
                  {t(`admin.tools.contact.outcome_${e.outcome}`, e.outcome)}
                </span>
              </p>
              {e.note && <p className="text-xs text-slate-600 mt-0.5 italic">&ldquo;{e.note}&rdquo;</p>}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

// ==================== ACTIONS ====================
function ActionsTab({ contract, onChanged, onClose }) {
  const { t } = useTranslation();
  const [busy, setBusy] = React.useState("");
  const [cancelReason, setCancelReason] = React.useState("");
  const [cancelNotify, setCancelNotify] = React.useState(true);
  const [showCancelForm, setShowCancelForm] = React.useState(false);

  const call = async (label, url, method = "post", body = null) => {
    setBusy(label);
    try {
      await api[method](url, body || {});
      toast.success(t("admin.tools.actions.done"));
      onChanged?.();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error");
    } finally {
      setBusy("");
    }
  };

  const doCancel = async () => {
    if (!window.confirm(t("admin.tools.actions.cancel_confirm"))) return;
    await call("cancel", `/admin/contracts/${contract.id}/cancel`, "post", {
      reason: cancelReason,
      notify_client: cancelNotify,
    });
    onClose?.();
  };

  const btnCls =
    "w-full text-left rounded-lg border border-slate-200 p-3 hover:bg-slate-50 transition flex items-center gap-3 disabled:opacity-50";

  return (
    <div data-testid="cmm-actions" className="space-y-2">
      <button
        onClick={() =>
          call("pdf", `/admin/contracts/${contract.id}/resend-pdf`)
        }
        disabled={busy === "pdf"}
        className={btnCls}
        data-testid="cmm-resend-pdf"
      >
        {busy === "pdf" ? (
          <Loader2 className="h-4 w-4 animate-spin text-[#5BA4D4]" />
        ) : (
          <RotateCcw className="h-4 w-4 text-[#5BA4D4]" />
        )}
        <span className="text-sm font-medium text-navy">
          {t("admin.tools.actions.resend_pdf")}
        </span>
      </button>

      <button
        onClick={() =>
          call("magic", `/admin/contracts/${contract.id}/resend-magic-link`)
        }
        disabled={busy === "magic"}
        className={btnCls}
        data-testid="cmm-resend-magic"
      >
        {busy === "magic" ? (
          <Loader2 className="h-4 w-4 animate-spin text-[#5BA4D4]" />
        ) : (
          <KeyRound className="h-4 w-4 text-[#5BA4D4]" />
        )}
        <span className="text-sm font-medium text-navy">
          {t("admin.tools.actions.resend_magic")}
        </span>
      </button>

      <div className="pt-3 border-t border-slate-200">
        {!showCancelForm ? (
          <button
            onClick={() => setShowCancelForm(true)}
            className="w-full text-left rounded-lg border border-red-200 bg-red-50 p-3 hover:bg-red-100 flex items-center gap-3"
            data-testid="cmm-open-cancel"
          >
            <Ban className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-red-700">
              {t("admin.tools.actions.cancel_rdv")}
            </span>
          </button>
        ) : (
          <div className="border border-red-200 bg-red-50 rounded-lg p-3">
            <p className="text-sm font-medium text-red-700 mb-2 flex items-center gap-2">
              <Ban className="h-4 w-4" /> {t("admin.tools.actions.cancel_rdv")}
            </p>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder={t("admin.tools.actions.cancel_reason")}
              rows={2}
              data-testid="cmm-cancel-reason"
              className="w-full rounded-md border border-red-200 px-3 py-2 text-sm mb-2"
            />
            <label className="flex items-center gap-2 text-xs text-slate-700 mb-3">
              <input
                type="checkbox"
                checked={cancelNotify}
                onChange={(e) => setCancelNotify(e.target.checked)}
                data-testid="cmm-cancel-notify"
              />
              {t("admin.tools.actions.cancel_notify")}
            </label>
            <div className="flex gap-2">
              <button
                onClick={doCancel}
                disabled={busy === "cancel"}
                data-testid="cmm-cancel-confirm"
                className="flex-1 rounded-md bg-red-600 hover:bg-red-700 text-white text-sm font-medium py-2 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {busy === "cancel" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
                {t("admin.tools.actions.cancel_rdv")}
              </button>
              <button
                onClick={() => setShowCancelForm(false)}
                className="rounded-md border border-slate-300 text-slate-600 text-sm px-3 py-2 hover:bg-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
