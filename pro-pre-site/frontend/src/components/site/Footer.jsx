import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Phone, Mail, MessageCircle } from "lucide-react";
import { BRAND } from "@/lib/api";
import { LEGAL_INFO } from "@/lib/legal";

export default function Footer() {
  const { t } = useTranslation();
  return (
    <footer className="bg-navy" id="contact">
      <div className="container-narrow py-16 text-white">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="rounded-xl bg-white p-2">
                <img src="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/89z1mmv7_4FE6D8C7-4FFC-421A-947D-FEC6CFFD80D7.png" alt="Pro-pre" className="h-8 w-auto" />
              </div>
              <div>
                <p className="font-bold text-lg">Pro-pre</p>
                <p className="text-xs text-slate-400">Nettoyage textile à domicile</p>
              </div>
            </div>
            <p className="text-sm text-slate-300">{t("voisin.body")}</p>
          </div>

          <div>
            <h4 className="eyebrow text-[#5BA4D4] mb-3">{t("footer.contact")}</h4>
            <a href={`tel:${BRAND.phone}`} className="flex items-center gap-2 py-1 text-sm hover:text-[#5BA4D4]" data-testid="footer-phone">
              <Phone className="h-4 w-4" /> {BRAND.phone}
            </a>
            <a href={`mailto:${BRAND.email}`} className="flex items-center gap-2 py-1 text-sm hover:text-[#5BA4D4]" data-testid="footer-email">
              <Mail className="h-4 w-4" /> {BRAND.email}
            </a>
            <a href={`https://wa.me/${BRAND.whatsapp.replace(/[^0-9]/g,'')}`} target="_blank" rel="noreferrer" className="flex items-center gap-2 py-1 text-sm hover:text-[#5BA4D4]" data-testid="footer-whatsapp">
              <MessageCircle className="h-4 w-4" /> WhatsApp
            </a>
          </div>

          <div>
            <h4 className="eyebrow text-[#5BA4D4] mb-3">Liens</h4>
            <a href="/#services" className="block py-1 text-sm text-slate-300 hover:text-white">{t("nav.services")}</a>
            <a href="/#defi" className="block py-1 text-sm text-slate-300 hover:text-white">{t("nav.defi")}</a>
            <Link to="/booking" className="block py-1 text-sm text-slate-300 hover:text-white">{t("nav.booking")}</Link>
            <a
              href="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/s3drmcj4_F7B86C9D-E7E4-48C9-B91F-EF76B5EE1F21.png"
              download="pro-pre-flyer.png"
              target="_blank"
              rel="noreferrer"
              className="block py-1 text-sm text-slate-300 hover:text-white"
              data-testid="footer-flyer-download"
            >
              Télécharger le flyer
            </a>
            <Link to="/admin" className="block py-1 text-sm text-slate-300 hover:text-white">{t("nav.admin")}</Link>
          </div>

          <div>
            <h4 className="eyebrow text-[#5BA4D4] mb-3">{t("zones.title")}</h4>
            <p className="text-sm text-slate-300">{t("zones.body")}</p>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-white/10 text-xs text-slate-400 flex flex-col sm:flex-row justify-between gap-3">
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-5">
            <span>© {new Date().getFullYear()} {BRAND.name}. {t("footer.rights")}.</span>
            <div className="flex gap-4 flex-wrap">
              <Link to="/privacy" className="hover:text-white" data-testid="footer-privacy">{t("footer.privacy")}</Link>
              <Link to="/mentions-legales" className="hover:text-white" data-testid="footer-legal">{t("footer.legal")}</Link>
              <Link to="/cgv" className="hover:text-white" data-testid="footer-cgv">{t("footer.cgv")}</Link>
            </div>
          </div>
          <span className="font-semibold tracking-widest text-yellow-400">RAPIDE · PROPRE · EFFICACE · RÉSULTAT GARANTI</span>
        </div>

        <p
          className="mt-4 text-[10px] text-slate-500 leading-relaxed max-w-3xl"
          data-testid="footer-legal-line"
        >
          {LEGAL_INFO.entityName} · {LEGAL_INFO.legalStatus} · SIRET&nbsp;978&nbsp;548&nbsp;329&nbsp;00017 · APE&nbsp;7022Z · {LEGAL_INFO.address}, {LEGAL_INFO.country} · {LEGAL_INFO.vat}
        </p>
      </div>
    </footer>
  );
}
