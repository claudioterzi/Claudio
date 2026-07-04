import React from "react";
import { Link } from "react-router-dom";
import { LEGAL_INFO } from "@/lib/legal";
import { Scale } from "lucide-react";

const L = LEGAL_INFO;

export default function MentionsLegales() {
  return (
    <div className="section">
      <div className="container-narrow max-w-3xl" data-testid="legal-page">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4]">
            <Scale className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-[#5BA4D4] font-semibold">Pro-pre</p>
            <h1 className="text-3xl sm:text-4xl font-semibold text-navy">Mentions légales</h1>
          </div>
        </div>

        <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
          <p className="text-sm text-slate-500 italic">
            Ce document est disponible uniquement en français, langue officielle de l'entreprise Pro-pre.
            <br />
            Dernière mise à jour : <b>{L.lastUpdate}</b>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">1. Éditeur du site</h2>
          <ul>
            <li><b>Nom / Dénomination</b> : {L.entityName}</li>
            <li><b>Statut juridique</b> : {L.legalStatus}</li>
            <li><b>Adresse du siège</b> : {L.address}</li>
            <li><b>Pays</b> : {L.country}</li>
            <li><b>Numéro d'entreprise / TVA</b> : {L.vat}</li>
            <li><b>Registre</b> : {L.rcs}</li>
            <li><b>Directeur de la publication</b> : {L.entityName}</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">2. Contact</h2>
          <ul>
            <li>Email : <a href={`mailto:${L.email}`} className="text-[#5BA4D4]">{L.email}</a></li>
            <li>Téléphone : <a href={`tel:${L.phone.replace(/\s/g,'')}`} className="text-[#5BA4D4]">{L.phone}</a></li>
            <li>WhatsApp : {L.whatsapp}</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">3. Hébergement</h2>
          <p>
            Le site est hébergé par : <b>{L.hostingProvider}</b>
            <br />
            Contact hébergeur : <a href={`mailto:${L.hostingContact}`} className="text-[#5BA4D4]">{L.hostingContact}</a>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">4. Domaines</h2>
          <ul>
            <li>{L.domainPrimary} (principal)</li>
            <li>{L.domainSecondary} (redirection)</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">5. Propriété intellectuelle</h2>
          <p>
            L'ensemble du contenu du site (textes, images, logo Pro-pre, code source, photographies) est protégé par le droit d'auteur et le droit des marques.
            Toute reproduction ou représentation, totale ou partielle, sans autorisation écrite préalable de {L.entityName}, est interdite et constitue une contrefaçon sanctionnée par les articles L335-2 et suivants du Code de la propriété intellectuelle.
          </p>
          <p>
            Les photographies "avant/après" affichées dans la galerie publique sont publiées avec le consentement explicite des clients concernés (art. 9 RGPD).
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">6. Assurance professionnelle</h2>
          <p>
            L'activité est couverte par une assurance Responsabilité Civile Professionnelle :
            <br />
            Compagnie : {L.insurance}
            <br />
            Numéro de police : {L.insuranceNumber}
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">7. Litiges et médiation</h2>
          <p>
            En cas de litige, une solution amiable sera recherchée en priorité. À défaut, le consommateur peut saisir, à son choix, les juridictions du lieu de son domicile ou celles du siège de l'entreprise.
            <br />
            Droit applicable : {L.applicableLaw}
          </p>
          <p>
            Les consommateurs peuvent également recourir à un médiateur de la consommation ou à la plateforme européenne de résolution en ligne des litiges :
            {" "}<a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-[#5BA4D4]">ec.europa.eu/consumers/odr</a>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">8. Crédits</h2>
          <p>
            Photographies : Claudio Terzi (photos "avant/après" avec consentement clients) — images d'illustration : bibliothèques libres de droits.
            <br />
            Icônes : Lucide (licence ISC).
            <br />
            Développement : réalisé sur la plateforme Emergent.
          </p>

          <div className="mt-10 pt-6 border-t border-slate-200 text-sm text-slate-500">
            Voir aussi : <Link to="/privacy" className="text-[#5BA4D4]">Politique de confidentialité</Link>
            {" · "}
            <Link to="/cgv" className="text-[#5BA4D4]">Conditions générales de vente</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
