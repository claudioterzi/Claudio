import React from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "@/lib/api";
import { Check, Loader2, X, ArrowRight } from "lucide-react";

const MAX_POLLS = 10;
const POLL_INTERVAL_MS = 2000;

export default function PaymentSuccess() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = React.useState("polling"); // polling | success | expired | failed | error
  const [attempts, setAttempts] = React.useState(0);
  const [amount, setAmount] = React.useState(null);

  React.useEffect(() => {
    if (!sessionId) {
      setState("error");
      return;
    }
    let cancelled = false;

    const poll = async (n) => {
      if (cancelled) return;
      if (n >= MAX_POLLS) {
        setState((s) => (s === "polling" ? "expired" : s));
        return;
      }
      try {
        const r = await api.get(`/checkout/status/${sessionId}`);
        if (cancelled) return;
        setAttempts(n + 1);
        if (r.data.amount_total) setAmount((r.data.amount_total / 100).toFixed(2));
        if (r.data.payment_status === "paid") {
          setState("success");
          return;
        }
        if (r.data.status === "expired" || r.data.payment_status === "failed") {
          setState("failed");
          return;
        }
        setTimeout(() => poll(n + 1), POLL_INTERVAL_MS);
      } catch {
        if (!cancelled) setState("error");
      }
    };
    poll(0);
    return () => { cancelled = true; };
  }, [sessionId]);

  const icon = {
    polling: <Loader2 className="h-10 w-10 animate-spin text-[#5BA4D4]" />,
    success: <Check className="h-10 w-10 text-emerald-500" />,
    expired: <X className="h-10 w-10 text-slate-400" />,
    failed: <X className="h-10 w-10 text-red-500" />,
    error: <X className="h-10 w-10 text-red-500" />,
  }[state];

  const title = {
    polling: t("payment.verifying"),
    success: t("payment.success_title"),
    expired: t("payment.expired_title"),
    failed: t("payment.failed_title"),
    error: t("payment.error_title"),
  }[state];

  const body = {
    polling: t("payment.verifying_body"),
    success: t("payment.success_body", { amount: amount ? `€${amount}` : "" }),
    expired: t("payment.expired_body"),
    failed: t("payment.failed_body"),
    error: t("payment.error_body"),
  }[state];

  return (
    <div className="section">
      <div className="container-narrow max-w-lg text-center">
        <div className="card-clean p-8" data-testid={`payment-status-${state}`}>
          <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${
            state === "success" ? "bg-emerald-100" :
            state === "polling" ? "bg-[#5BA4D4]/10" :
            "bg-slate-100"
          }`}>{icon}</div>
          <h1 className="mt-5 text-2xl font-semibold text-navy">{title}</h1>
          <p className="mt-2 text-slate-600 text-sm">{body}</p>
          {state === "polling" && (
            <p className="mt-3 text-xs text-slate-400">{t("payment.attempt")} {attempts}/{MAX_POLLS}</p>
          )}
          {(state === "success" || state === "failed" || state === "expired" || state === "error") && (
            <div className="mt-6 flex flex-col gap-2">
              <button
                onClick={() => navigate("/mon-espace")}
                className="btn-primary justify-center"
                data-testid="payment-go-space"
              >
                {t("payment.go_space")} <ArrowRight className="h-4 w-4" />
              </button>
              {state !== "success" && (
                <button
                  onClick={() => navigate("/defi")}
                  className="btn-outline justify-center"
                  data-testid="payment-retry"
                >
                  {t("payment.retry")}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
