import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api, API } from "@/lib/api";
import { Sparkles, Droplets, Wind, Shield, Star, MapPin, ChevronRight, Sofa, Bed, Car, Footprints, Download, MessageCircle, Check } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import ShareButton from "@/components/site/ShareButton";

const HERO_IMG = "https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/a83zvxnk_3869683F-2E1D-401A-AA72-80DBCB98BFA6.png";
const SOFA_IMG = "https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/a83zvxnk_3869683F-2E1D-401A-AA72-80DBCB98BFA6.png";
const CLAUDIO_IMG = "https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/a83zvxnk_3869683F-2E1D-401A-AA72-80DBCB98BFA6.png";
const BRUSSELS_IMG = "https://images.unsplash.com/photo-1701013694884-a278c7acea5c";

const SERVICE_ICONS = {
  canape_2: Sofa, canape_3: Sofa, canape_ang: Sofa,
  matelas_1: Bed, matelas_2: Bed,
  tapis: Sparkles, escaliers: Footprints, auto: Car,
};

function PublicGallery() {
  const { t } = useTranslation();
  const [items, setItems] = React.useState([]);
  React.useEffect(() => { api.get("/gallery").then(r => setItems(r.data.items || [])).catch(()=>{}); }, []);
  if (!items.length) return null;
  return (
    <section className="section" data-testid="public-gallery-section">
      <div className="container-narrow">
        <p className="eyebrow">{t("gallery_pub.eyebrow")}</p>
        <h2 className="mt-2 text-3xl sm:text-4xl font-semibold text-navy">{t("gallery_pub.title")}</h2>
        <p className="mt-3 text-slate-600 max-w-2xl">{t("gallery_pub.body")}</p>
        <div className="mt-8 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="public-gallery-grid">
          {items.slice(0, 8).map(it => (
            <a key={it.id} href={`${API}/gallery/${it.storage_path}`} target="_blank" rel="noreferrer" className="card-clean overflow-hidden group" data-testid={`gallery-public-${it.id}`}>
              <img src={`${API}/gallery/${it.storage_path}`} alt={it.caption} loading="lazy" className="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-105" />
              {it.caption && <p className="p-3 text-xs text-slate-600">{it.caption}</p>}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const { t } = useTranslation();

  const services = [
    { id: "canape_2", price: 80, unit: "fixe" },
    { id: "canape_3", price: 110, unit: "fixe" },
    { id: "canape_ang", price: 150, unit: "fixe" },
    { id: "matelas_1", price: 65, unit: "fixe" },
    { id: "matelas_2", price: 90, unit: "fixe" },
    { id: "tapis", price: 20, unit: "m2" },
    { id: "escaliers", price: 7, unit: "marche" },
    { id: "auto", price: 100, unit: "fixe" },
  ];

  const testimonials = t("testimonials.items", { returnObjects: true });

  const faqItems = t("faq.items", { returnObjects: true });

  const unitLabel = (u) => u === "m2" ? t("services.per_m2") : u === "marche" ? t("services.per_step") : "";

  return (
    <div data-testid="home-root">
      {/* HERO */}
      <section className="relative overflow-hidden" data-testid="hero-section">
        <div className="absolute inset-0">
          <img src={HERO_IMG} alt="" className="h-full w-full object-cover object-[center_20%] opacity-25" />
          <div className="absolute inset-0 bg-gradient-to-b from-white via-white/85 to-white" />
        </div>
        <div className="container-narrow relative pt-16 pb-20 sm:pt-24 sm:pb-28">
          <div className="max-w-3xl">
            <p className="eyebrow fade-up">{t("hero.eyebrow")}</p>
            <h1 className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-navy fade-up">
              {t("hero.title")}
            </h1>
            <p className="mt-5 text-lg text-slate-600 max-w-2xl fade-up">{t("hero.subtitle")}</p>

            {/* Benefits row from flyer */}
            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-700 fade-up">
              {t("hero_benefits", { returnObjects: true }).map((b, i) => (
                <span key={`hb-${i}-${b}`} className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#5BA4D4]" /> {b}</span>
              ))}
            </div>

            <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-yellow-100 border border-yellow-400 px-4 py-2 text-sm text-[#1B2845] fade-up" data-testid="promo-banner">
              <span className="rounded-full bg-yellow-400 text-[#1B2845] px-2 py-0.5 text-xs font-bold tracking-wide">VOISIN20</span>
              <span>{t("hero.promo")}</span>
            </div>

            <div className="mt-8 flex flex-col sm:flex-row gap-3 fade-up">
              <Link to="/defi" className="btn-secondary" data-testid="hero-defi-cta">
                <Sparkles className="h-5 w-5" /> {t("hero.cta_defi")}
              </Link>
              <Link to="/booking" className="btn-primary" data-testid="hero-book-cta">
                {t("hero.cta_book")} <ChevronRight className="h-5 w-5" />
              </Link>
            </div>
            <div className="mt-10 flex flex-wrap gap-6 text-sm text-slate-600">
              <span className="flex items-center gap-2"><Shield className="h-4 w-4 text-[#5BA4D4]" /> Kärcher Pro</span>
              <span className="flex items-center gap-2"><MapPin className="h-4 w-4 text-[#5BA4D4]" /> Bruxelles · Paris · Bergamo</span>
              <span className="flex items-center gap-2"><Star className="h-4 w-4 text-[#5BA4D4]" /> {t("hero.payments")}</span>
            </div>
          </div>
        </div>
      </section>

      {/* DÉFI DE LA BANDE — 3 steps like flyer */}
      <section id="defi" className="section bg-soft" data-testid="defi-section">
        <div className="container-narrow">
          <div className="text-center max-w-2xl mx-auto">
            <p className="eyebrow">{t("defi.kicker")}</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-semibold text-navy">{t("defi.title")}</h2>
            <p className="mt-4 text-lg text-slate-600">{t("defi.body")}</p>
          </div>

          {/* Hero image showing the challenge in action */}
          <div className="mt-10 rounded-2xl overflow-hidden shadow-xl border border-white ring-1 ring-slate-200" data-testid="defi-hero-image">
            <img
              src="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/f957gsid_432DC520-5482-4758-88C4-F9166AA76E99.png"
              alt="Le Défi de la Bande — bande propre de 30 × 30 cm sur canapé"
              className="w-full h-auto object-cover"
              loading="lazy"
            />
          </div>

          <div className="mt-10 grid md:grid-cols-3 gap-6">
            {[
              { n: "1", icon: Droplets, t: t("defi.steps.s1_t"), d: t("defi.steps.s1_d") },
              { n: "2", icon: Sparkles, t: t("defi.steps.s2_t"), d: t("defi.steps.s2_d") },
              { n: "3", icon: Check, t: t("defi.steps.s3_t"), d: t("defi.steps.s3_d") },
            ].map((s) => (
              <div key={`defi-step-${s.n}`} className="card-clean p-6 relative" data-testid={`defi-step-${s.n}`}>
                <div className="absolute -top-3 -left-3 h-9 w-9 rounded-full bg-[#5BA4D4] text-white flex items-center justify-center font-bold text-lg shadow-md">{s.n}</div>
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4] ml-6"><s.icon className="h-5 w-5" /></div>
                <h3 className="mt-4 text-lg font-semibold text-navy">{s.t}</h3>
                <p className="mt-2 text-sm text-slate-600">{s.d}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 text-center">
            <Link to="/defi" className="btn-secondary" data-testid="defi-cta">{t("defi.cta")}</Link>
            <p className="mt-3 text-xs text-slate-500">{t("defi.footer_note")}</p>
          </div>
        </div>
      </section>

      {/* SERVICES */}
      <section id="services" className="section" data-testid="services-section">
        <div className="container-narrow">
          <div className="max-w-2xl">
            <p className="eyebrow">Tarifs</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-semibold text-navy">{t("services.title")}</h2>
            <p className="mt-3 text-slate-600">{t("services.subtitle")}</p>
          </div>

          <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {services.map((s, i) => {
              const Icon = SERVICE_ICONS[s.id] || Sparkles;
              return (
                <div key={s.id} className="card-clean p-6 fade-up" style={{ animationDelay: `${i*60}ms` }} data-testid={`service-card-${s.id}`}>
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-navy">{t(`services.items.${s.id}.name`)}</h3>
                  <p className="mt-1 text-sm text-slate-500">{t(`services.items.${s.id}.desc`)}</p>
                  <div className="mt-4 flex items-baseline gap-1">
                    <span className="text-xs text-slate-500">{t("services.from")}</span>
                    <span className="text-2xl font-bold text-navy">€{s.price}</span>
                    <span className="text-sm text-slate-500">{unitLabel(s.unit)}</span>
                  </div>
                  <Link to="/booking" state={{ preselect: s.id }} className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[#5BA4D4] hover:text-[#1B2845]" data-testid={`service-book-${s.id}`}>
                    {t("services.cta")} <ChevronRight className="h-4 w-4" />
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* PROOF — dirty water */}
      <section className="section bg-navy text-white overflow-hidden" data-testid="proof-section">
        <div className="container-narrow grid lg:grid-cols-2 gap-12 items-center">
          <div className="relative rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 order-2 lg:order-1">
            <img
              src="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/wgc8ik6b_E47C6F16-5515-4B07-A853-EEE6B18043BE.png"
              alt="L'eau extraite après nettoyage Kärcher"
              className="w-full h-auto object-cover"
              loading="lazy"
            />
            <div className="absolute bottom-4 left-4 right-4 bg-yellow-400 text-[#1B2845] rounded-lg px-4 py-2 font-bold text-sm tracking-wide shadow-lg">
              {t("proof.badge")}
            </div>
          </div>
          <div className="order-1 lg:order-2">
            <p className="eyebrow !text-yellow-400">{t("proof.eyebrow")}</p>
            <h2 className="mt-3 text-3xl sm:text-4xl lg:text-5xl font-bold leading-tight">
              {t("proof.title")}
            </h2>
            <p className="mt-5 text-lg text-slate-200">
              {t("proof.body_1")}
              <br/><span className="font-semibold text-white">{t("proof.body_2")}</span>
            </p>
            <div className="mt-8 space-y-3">
              {t("proof.items", { returnObjects: true }).map((it, i) => (
                <div key={`proof-${i}-${it.slice?.(0,20)}`} className="flex items-start gap-3" data-testid={`proof-item-${i}`}>
                  <div className="mt-1 h-2 w-2 rounded-full bg-yellow-400 flex-shrink-0" />
                  <span className="text-slate-200">{it}</span>
                </div>
              ))}
            </div>
            <div className="mt-8 rounded-xl bg-white/5 border border-white/10 p-5">
              <p className="text-lg font-semibold">{t("proof.cta_head")}</p>
              <p className="mt-1 text-sm text-slate-300">{t("proof.cta_sub")}</p>
              <Link to="/defi" className="btn-secondary mt-5" data-testid="proof-cta">
                <Sparkles className="h-5 w-5" /> {t("proof.cta_btn")}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* TECH */}
      <section className="section bg-navy text-white" data-testid="tech-section">
        <div className="container-narrow">
          <div className="max-w-2xl">
            <p className="eyebrow">Kärcher Pro</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-semibold">{t("tech.title")}</h2>
            <p className="mt-3 text-slate-300">{t("tech.subtitle")}</p>
          </div>
          <div className="mt-10 grid md:grid-cols-3 gap-6">
            {[
              { icon: Droplets, t: t("tech.step1_t"), d: t("tech.step1_d") },
              { icon: Sparkles, t: t("tech.step2_t"), d: t("tech.step2_d") },
              { icon: Wind, t: t("tech.step3_t"), d: t("tech.step3_d") },
            ].map((s, i) => (
              <div key={`tech-${i}-${s.t}`} className="rounded-2xl border border-white/10 bg-white/5 p-6" data-testid={`tech-step-${i+1}`}>
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#5BA4D4] text-white"><s.icon className="h-6 w-6" /></div>
                <h3 className="mt-4 text-xl font-semibold">{i+1}. {s.t}</h3>
                <p className="mt-2 text-slate-300">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VOISIN */}
      <section className="section" data-testid="voisin-section">
        <div className="container-narrow grid lg:grid-cols-2 gap-12 items-center">
          <div className="relative">
            <img src={CLAUDIO_IMG} alt="Claudio" className="rounded-2xl w-full h-[420px] object-cover object-[center_15%] shadow-lg" />
            <div className="absolute -bottom-4 -right-4 bg-[#5BA4D4] text-white rounded-2xl px-5 py-3 shadow-lg">
              <p className="text-xs uppercase tracking-wider opacity-80">{t("voisin.title")}</p>
              <p className="text-lg font-semibold">Claudio · Bruxelles</p>
            </div>
          </div>
          <div>
            <p className="eyebrow">{t("why.heading")}</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-semibold text-navy">{t("voisin.title")}</h2>
            <p className="mt-4 text-lg text-slate-600">{t("voisin.body")}</p>

            {/* Pourquoi nous choisir - checklist from flyer */}
            <div className="mt-8 space-y-3">
              {t("why.items", { returnObjects: true }).map((it, i) => (
                <div key={`why-${i}-${it.slice?.(0,20)}`} className="flex items-start gap-3" data-testid={`why-item-${i}`}>
                  <div className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-[#5BA4D4] text-white"><Check className="h-3 w-3" /></div>
                  <span className="text-slate-700">{it}</span>
                </div>
              ))}
            </div>

            <a href="#contact" className="btn-outline mt-8" data-testid="voisin-cta">{t("voisin.cta")}</a>
          </div>
        </div>
      </section>

      {/* PUBLIC GALLERY */}
      <PublicGallery />

      {/* TESTIMONIALS */}
      <section className="section bg-soft" data-testid="testimonials-section">
        <div className="container-narrow">
          <h2 className="text-3xl sm:text-4xl font-semibold text-navy">{t("testimonials.title")}</h2>
          <div className="mt-10 grid md:grid-cols-3 gap-5">
            {Array.isArray(testimonials) && testimonials.map((tt, i) => (
              <div key={tt.id || `testimonial-${i}-${tt.name}`} className="card-clean p-6" data-testid={`testimonial-${i}`}>
                <div className="flex gap-1 text-[#5BA4D4]">
                  {Array.from({length: 5}).map((_,j) => <Star key={`star-${tt.id||i}-${j}`} className="h-4 w-4 fill-current" />)}
                </div>
                <p className="mt-4 text-slate-700">&ldquo;{tt.text}&rdquo;</p>
                <p className="mt-4 text-sm text-slate-500">— {tt.name}, {tt.city}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ZONES */}
      <section className="section" data-testid="zones-section">
        <div className="container-narrow grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <p className="eyebrow"><MapPin className="inline h-4 w-4 mr-1" />{t("zones.title")}</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-semibold text-navy">{t("zones.title")}</h2>
            <p className="mt-4 text-slate-600">{t("zones.body")}</p>
          </div>
          <img src={BRUSSELS_IMG} alt="Brussels" className="rounded-2xl h-72 w-full object-cover" />
        </div>
      </section>

      {/* FLYER DOWNLOAD */}
      <section className="section bg-soft" data-testid="flyer-section">
        <div className="container-narrow grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <p className="eyebrow">{t("flyer.eyebrow")}</p>
            <h2 className="mt-2 text-3xl sm:text-4xl font-semibold text-navy">{t("flyer.title")}</h2>
            <p className="mt-4 text-lg text-slate-600">{t("flyer.body")}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/s3drmcj4_F7B86C9D-E7E4-48C9-B91F-EF76B5EE1F21.png"
                download="pro-pre-flyer.png"
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                data-testid="flyer-download-btn"
              >
                <Download className="h-5 w-5" /> {t("flyer.download")}
              </a>
              <a
                href={`https://wa.me/?text=${encodeURIComponent(t("flyer.wa_msg"))}`}
                target="_blank"
                rel="noreferrer"
                className="btn-outline"
                data-testid="flyer-share-btn"
              >
                <MessageCircle className="h-5 w-5" /> {t("flyer.share")}
              </a>
            </div>
          </div>
          <a
            href="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/s3drmcj4_F7B86C9D-E7E4-48C9-B91F-EF76B5EE1F21.png"
            target="_blank"
            rel="noreferrer"
            className="block card-clean overflow-hidden group"
            data-testid="flyer-preview"
          >
            <img
              src="https://customer-assets.emergentagent.com/job_tissu-propre/artifacts/s3drmcj4_F7B86C9D-E7E4-48C9-B91F-EF76B5EE1F21.png"
              alt="Flyer Pro-pre"
              className="w-full h-auto transition-transform duration-500 group-hover:scale-[1.02]"
              loading="lazy"
            />
          </a>
        </div>
      </section>

      {/* JOIN US — Recruitment */}
      <section className="section" data-testid="join-section">
        <div className="container-narrow">
          <div className="rounded-3xl bg-gradient-to-br from-[#1B2845] to-[#293B61] p-8 sm:p-12 text-white text-center">
            <p className="eyebrow !text-[#5BA4D4]">{t("join.eyebrow")}</p>
            <h2 className="mt-3 text-3xl sm:text-4xl font-semibold">{t("join.title")}</h2>
            <p className="mt-4 max-w-2xl mx-auto text-slate-200">
              {t("join.body_1")}
              <br/><span className="font-semibold text-white">{t("join.body_2")}</span>
            </p>
            <a
              href="mailto:Terziclaudio@gmail.com?subject=Candidature%20Pro-pre&body=Bonjour%20Claudio%2C%0A%0AJe%20souhaite%20rejoindre%20Pro-pre%20dans%20la%20ville%20de%20%3A%20%0AMon%20expérience%20%3A%20%0AMes%20coordonnées%20%3A%20%0A%0A(Joindre%20CV%20en%20pièce%20jointe)"
              className="btn-secondary mt-8 inline-flex"
              data-testid="join-cta"
            >
              {t("join.cta")}
            </a>
            <p className="mt-4 text-xs text-slate-400">{t("join.hint")}</p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section bg-soft" data-testid="faq-section">
        <div className="container-narrow max-w-3xl">
          <h2 className="text-3xl sm:text-4xl font-semibold text-navy">{t("faq.title")}</h2>
          <Accordion type="single" collapsible className="mt-8" data-testid="faq-accordion">
            {Array.isArray(faqItems) && faqItems.map((it, i) => (
              <AccordionItem key={it.q || `faq-${i}`} value={`faq-${i}`} data-testid={`faq-item-${i}`}>
                <AccordionTrigger className="text-left text-navy font-medium">{it.q}</AccordionTrigger>
                <AccordionContent className="text-slate-600">{it.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* Share with neighbours banner */}
      <section className="section bg-navy text-white" data-testid="share-banner-section">
        <div className="container-narrow max-w-3xl text-center">
          <p className="eyebrow !text-[#5BA4D4]">{t("share.banner_kicker")}</p>
          <h2 className="mt-3 text-3xl sm:text-4xl font-semibold">{t("share.banner_title")}</h2>
          <p className="mt-3 text-slate-300">{t("share.banner_sub")}</p>
          <div className="mt-6 inline-block">
            <ShareButton variant="banner" />
          </div>
        </div>
      </section>
    </div>
  );
}
