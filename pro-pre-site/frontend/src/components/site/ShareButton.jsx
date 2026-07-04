import React from "react";
import { useTranslation } from "react-i18next";
import {
  Share2,
  Copy,
  Check,
  MessageCircle,
  Send,
  Facebook,
  Linkedin,
  Mail,
  X as XIcon,
} from "lucide-react";
import { toast } from "sonner";

const SHARE_URL = "https://www.pro-pre.com";

export default function ShareButton({ variant = "icon", className = "" }) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const menuRef = React.useRef(null);

  const shareTitle = t("share.title");
  const shareText = t("share.text");

  React.useEffect(() => {
    const onClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  const tryNativeShare = async (e) => {
    e?.stopPropagation?.();
    if (navigator.share) {
      try {
        await navigator.share({ title: shareTitle, text: shareText, url: SHARE_URL });
        return;
      } catch {
        /* user cancelled — silent */
      }
    }
    setOpen(true);
  };

  const encTxt = encodeURIComponent(`${shareText} ${SHARE_URL}`);
  const encUrl = encodeURIComponent(SHARE_URL);
  const encTitle = encodeURIComponent(shareTitle);

  const targets = [
    { id: "whatsapp", label: "WhatsApp", href: `https://wa.me/?text=${encTxt}`, icon: MessageCircle, color: "bg-green-500" },
    { id: "telegram", label: "Telegram", href: `https://t.me/share/url?url=${encUrl}&text=${encTitle}`, icon: Send, color: "bg-sky-500" },
    { id: "facebook", label: "Facebook", href: `https://www.facebook.com/sharer/sharer.php?u=${encUrl}`, icon: Facebook, color: "bg-blue-600" },
    { id: "linkedin", label: "LinkedIn", href: `https://www.linkedin.com/sharing/share-offsite/?url=${encUrl}`, icon: Linkedin, color: "bg-blue-700" },
    { id: "x", label: "X (Twitter)", href: `https://twitter.com/intent/tweet?url=${encUrl}&text=${encTitle}`, icon: XIcon, color: "bg-slate-900" },
    { id: "email", label: "Email", href: `mailto:?subject=${encTitle}&body=${encTxt}`, icon: Mail, color: "bg-slate-500" },
  ];

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(SHARE_URL);
      setCopied(true);
      toast.success(t("share.copied"));
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error(t("admin.error"));
    }
  };

  const btn = variant === "banner" ? (
    <button
      onClick={tryNativeShare}
      className={`btn-primary ${className}`}
      data-testid="share-btn-banner"
    >
      <Share2 className="h-4 w-4" /> {t("share.cta")}
    </button>
  ) : variant === "outline" ? (
    <button
      onClick={tryNativeShare}
      className={`btn-outline !py-2 !px-4 text-sm ${className}`}
      data-testid="share-btn-outline"
    >
      <Share2 className="h-4 w-4" /> {t("share.short")}
    </button>
  ) : (
    <button
      onClick={tryNativeShare}
      aria-label={t("share.short")}
      className={`flex items-center justify-center h-10 w-10 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 ${className}`}
      data-testid="share-btn-icon"
    >
      <Share2 className="h-4 w-4" />
    </button>
  );

  return (
    <div className="relative inline-block" ref={menuRef}>
      {btn}
      {open && (
        <div
          className="absolute right-0 mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl z-50"
          data-testid="share-menu"
        >
          <div className="p-3 border-b border-slate-100">
            <p className="text-xs uppercase tracking-wider font-semibold text-slate-500">{t("share.menu_title")}</p>
          </div>
          <div className="p-2 grid grid-cols-3 gap-1">
            {targets.map((tg) => (
              <a
                key={tg.id}
                href={tg.href}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setOpen(false)}
                className="flex flex-col items-center gap-1 rounded-lg p-2 hover:bg-slate-50 text-xs"
                data-testid={`share-${tg.id}`}
              >
                <span className={`h-9 w-9 rounded-full ${tg.color} text-white flex items-center justify-center`}>
                  <tg.icon className="h-4 w-4" />
                </span>
                <span className="text-slate-600">{tg.label}</span>
              </a>
            ))}
          </div>
          <button
            onClick={copyLink}
            className="w-full border-t border-slate-100 p-3 flex items-center gap-2 text-sm hover:bg-slate-50"
            data-testid="share-copy-link"
          >
            {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4 text-slate-500" />}
            <span className="text-slate-700 truncate flex-1 text-left">
              {copied ? t("share.copied") : SHARE_URL}
            </span>
          </button>
        </div>
      )}
    </div>
  );
}
