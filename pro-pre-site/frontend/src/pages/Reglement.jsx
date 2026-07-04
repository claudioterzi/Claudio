import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ShieldCheck,
  Sparkles,
  Wallet,
  Lock,
  Undo2,
  Phone,
  MessageCircle,
  Mail,
} from "lucide-react";
import { BRAND } from "@/lib/api";

/**
 * Réglement & Confiance — Simple, court, humain, mais légal.
 * A one-page overview reassuring the user about how everything works
 * (free band challenge, service, payment, data) — with links to the
 * full-detail legal pages (Privacy, CGV, Mentions Légales).
 */
export default function Reglement() {
  const { t } = useTranslation();

  const blocks = [
    {
      icon: Sparkles,
      color: "text-[#5BA4D4]",
      bg: "bg-[#5BA4D4]/10",
      title: t("reglement.defi_title"),
      body: t("reglement.defi_body"),
    },
    {
      icon: ShieldCheck,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      title: t("reglement.service_title"),
      body: t("reglement.service_body"),
    },
    {
      icon: Wallet,
      color: "text-amber-600",
      bg: "bg-amber-50",
      title: t("reglement.payment_title"),
      body: t("reglement.payment_body"),
    },
    {
      icon: Lock,
      color: "text-navy",
      bg: "bg-slate-100",
      title: t("reglement.data_title"),
      body: t("reglement.data_body"),
    },
    {
      icon: Undo2,
      color: "text-red-500",
      bg: "bg-red-50",
      title: t("reglement.rights_title"),
      body: t("reglement.rights_body"),
    },
  ];

  return (
    <div className="section" data-testid="reglement-page">
      <div className="container-narrow max-w-3xl">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 rounded-2xl bg-[#5BA4D4]/10 text-[#5BA4D4] flex items-center justify-center">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h1 className="mt-4 text-3xl sm:text-4xl font-bold text-navy">
            {t("reglement.title")}
          </h1>
          <p className="mt-3 text-slate-600 max-w-xl mx-auto">
            {t("reglement.subtitle")}
          </p>
        </div>

        <div className="mt-10 space-y-4">
          {blocks.map((b, i) => (
            <div
              key={i}
              className="card-clean p-5 flex gap-4"
              data-testid={`reglement-block-${i}`}
            >
              <div
                className={`h-10 w-10 rounded-xl ${b.bg} ${b.color} flex items-center justify-center flex-shrink-0`}
              >
                <b.icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="font-semibold text-navy">{b.title}</h2>
                <p className="mt-1 text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                  {b.body}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 card-clean p-6 bg-navy text-white" data-testid="reglement-contact">
          <h2 className="text-xl font-semibold">
            {t("reglement.contact_title")}
          </h2>
          <p className="mt-2 text-white/80 text-sm">
            {t("reglement.contact_body")}
          </p>
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-3 gap-3">
            <a
              href={`tel:${BRAND.phone}`}
              className="flex items-center gap-2 rounded-lg bg-white/10 hover:bg-white/20 px-4 py-3 transition"
              data-testid="reglement-call"
            >
              <Phone className="h-4 w-4" />
              <span className="text-sm font-medium">{t("reglement.call")}</span>
            </a>
            <a
              href={`https://wa.me/${(BRAND.phone || "").replace(/[^\d]/g, "")}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 px-4 py-3 transition"
              data-testid="reglement-whatsapp"
            >
              <MessageCircle className="h-4 w-4" />
              <span className="text-sm font-medium">WhatsApp</span>
            </a>
            <a
              href={`mailto:${BRAND.email}`}
              className="flex items-center gap-2 rounded-lg bg-white/10 hover:bg-white/20 px-4 py-3 transition"
              data-testid="reglement-email"
            >
              <Mail className="h-4 w-4" />
              <span className="text-sm font-medium">Email</span>
            </a>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap justify-center gap-3 text-sm">
          <Link to="/privacy" className="text-[#5BA4D4] hover:underline" data-testid="reglement-link-privacy">
            {t("footer.privacy")}
          </Link>
          <span className="text-slate-300">·</span>
          <Link to="/cgv" className="text-[#5BA4D4] hover:underline" data-testid="reglement-link-cgv">
            {t("footer.cgv")}
          </Link>
          <span className="text-slate-300">·</span>
          <Link to="/mentions-legales" className="text-[#5BA4D4] hover:underline" data-testid="reglement-link-legal">
            {t("footer.legal")}
          </Link>
        </div>
      </div>
    </div>
  );
}
