import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Cookie, X } from "lucide-react";

const STORAGE_KEY = "pro-pre.cookie-consent.v1";

export default function CookieBanner() {
  const { t } = useTranslation();
  const [visible, setVisible] = React.useState(false);

  React.useEffect(() => {
    try {
      const done = localStorage.getItem(STORAGE_KEY);
      if (!done) {
        // Delay to avoid CLS on first paint
        setTimeout(() => setVisible(true), 800);
      }
    } catch {
      /* localStorage unavailable — skip banner */
    }
  }, []);

  const record = (choice) => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ choice, at: Date.now() }),
      );
    } catch {
      /* ignore */
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      className="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:max-w-md z-40 animate-in slide-in-from-bottom duration-500"
      data-testid="cookie-banner"
      role="dialog"
      aria-label="Cookie notice"
    >
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-5">
        <div className="flex items-start gap-3">
          <div className="h-9 w-9 rounded-lg bg-[#5BA4D4]/10 text-[#5BA4D4] flex items-center justify-center flex-shrink-0">
            <Cookie className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-navy">{t("cookie.title")}</p>
            <p className="text-xs text-slate-600 mt-1">
              {t("cookie.body")}{" "}
              <Link to="/privacy" className="text-[#5BA4D4] underline">
                {t("cookie.learn")}
              </Link>
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={() => record("accepted")}
                className="btn-primary !py-2 !px-4 text-sm"
                data-testid="cookie-accept"
              >
                {t("cookie.accept")}
              </button>
              <button
                onClick={() => record("refused")}
                className="btn-outline !py-2 !px-4 text-sm"
                data-testid="cookie-refuse"
              >
                {t("cookie.refuse")}
              </button>
            </div>
          </div>
          <button
            onClick={() => record("dismissed")}
            aria-label="Close"
            className="text-slate-400 hover:text-slate-600 p-1"
            data-testid="cookie-close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
