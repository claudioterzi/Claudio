import React from "react";
import { Link } from "react-router-dom";
import { LEGAL_INFO } from "@/lib/legal";
import { FileText } from "lucide-react";

const L = LEGAL_INFO;

export default function CGV() {
  return (
    <div className="section">
      <div className="container-narrow max-w-3xl" data-testid="cgv-page">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4]">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-[#5BA4D4] font-semibold">Pro-pre</p>
            <h1 className="text-3xl sm:text-4xl font-semibold text-navy">Conditions générales de vente</h1>
          </div>
        </div>

        <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
          <p className="text-sm text-slate-500 italic">
            Ce document est disponible uniquement en français, langue officielle de l'entreprise Pro-pre.
            <br />
            Dernière mise à jour : <b>{L.lastUpdate}</b>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 1 — Objet</h2>
          <p>
            Les présentes Conditions Générales de Vente (CGV) régissent les prestations de <b>nettoyage textile professionnel à domicile</b>
            fournies par <b>{L.entityName}</b> ("Pro-pre") au consommateur ("le Client"), via les sites www.pro-pre.com et www.pro-pre.fr.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 2 — Services proposés</h2>
          <ul>
            <li>Nettoyage de canapés (2 places, 3 places, d'angle)</li>
            <li>Nettoyage de matelas (1 place, 2 places)</li>
            <li>Nettoyage de tapis (au m²)</li>
            <li>Nettoyage d'escaliers en moquette (à la marche)</li>
            <li>Nettoyage de sièges automobiles</li>
            <li>Test gratuit "Défi de la Bande" (bande de 30 × 30 cm sur la zone la plus sale, sans engagement)</li>
          </ul>
          <p>
            Technologie utilisée : injection-extraction Kärcher (nettoyage en profondeur avec eau et détergent doux).
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 3 — Zone géographique</h2>
          <p>
            Le service est actuellement proposé sur <b>{L.serviceZone}</b>. Une extension vers Paris et Bergamo est prévue (avec inscription à la liste d'attente).
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 4 — Prix</h2>
          <p>
            Les tarifs affichés sur le site sont exprimés en euros (€) et sont indicatifs. Un devis définitif est communiqué avant le début du service.
          </p>
          <p>
            <b>Le "Défi de la Bande" est 100 % gratuit</b>, sans obligation d'achat. Aucun frais de déplacement n'est facturé pour cette prestation initiale.
          </p>
          <p>
            En cas de nettoyage complet confirmé après le test, le prix est celui du devis accepté par le Client.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 5 — Réservation et acompte</h2>
          <p>
            La réservation s'effectue en ligne via le formulaire dédié. Un acompte optionnel de <b>30 €</b> peut être demandé pour bloquer un créneau,
            selon trois modalités au choix du Client :
          </p>
          <ul>
            <li><b>Carte bancaire</b> via Stripe (paiement sécurisé en ligne)</li>
            <li><b>Virement bancaire</b> (IBAN communiqué après confirmation)</li>
            <li><b>Espèces</b> à l'arrivée du technicien</li>
          </ul>
          <p>
            L'acompte est <b>déduit du prix final</b> si le service complet est confirmé. Il est <b>remboursé intégralement</b> en cas d'annulation par Pro-pre.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 6 — Paiement</h2>
          <p>
            Le solde est dû à la fin de la prestation, aux modalités convenues avec le technicien (espèces, virement, ou Stripe).
            Aucun paiement complet n'est exigé avant le service.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 7 — Droit de rétractation (Consommateurs)</h2>
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg my-4">
            <p className="!mt-0">
              🛡️ <b>Vous disposez d'un délai de 14 jours</b> pour vous rétracter à compter de la conclusion du contrat, sans avoir à justifier de motif ni à payer de pénalité (art. L221-18 du Code de la consommation français ; art. VI.47 du Code de droit économique belge pour les consommateurs belges).
            </p>
          </div>
          <p>
            <b>Exception</b> : si le Client demande expressément l'exécution du service avant l'expiration du délai de 14 jours et reconnaît par écrit qu'il perdra son droit de rétractation une fois le service pleinement exécuté, le droit de rétractation ne s'applique plus (art. L221-25 du Code de la consommation ; art. VI.53, 13° CDE belge).
          </p>
          <p>
            Pour exercer votre droit de rétractation, envoyez un email à <a href={`mailto:${L.email}?subject=Rétractation`} className="text-[#5BA4D4]">{L.email}</a>
            {" "}en indiquant le numéro de contrat (visible sur le PDF envoyé par email).
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 8 — Annulation par le Client (hors droit de rétractation)</h2>
          <ul>
            <li>Annulation gratuite jusqu'à 24 h avant le rendez-vous</li>
            <li>Entre 24 h et 2 h avant : acompte non remboursable (30 €)</li>
            <li>Moins de 2 h ou absence du Client : l'intégralité du prix du service peut être facturée</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 9 — Responsabilité et garanties</h2>
          <p>
            Pro-pre s'engage à intervenir avec soin et professionnalisme, dans le respect des règles de l'art.
            En cas de détérioration causée par le technicien, Pro-pre est couvert par son <b>assurance Responsabilité Civile Professionnelle</b>
            {" "}({L.insurance}, police n° {L.insuranceNumber}).
          </p>
          <p>
            Pro-pre ne peut être tenu responsable :
          </p>
          <ul>
            <li>de l'usure préexistante du bien traité</li>
            <li>de taches indélébiles impossibles à retirer malgré nos efforts (identifiées lors du test préalable)</li>
            <li>des dommages causés par une utilisation ultérieure inadaptée du bien</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 10 — Photos avant/après</h2>
          <p>
            Le Client autorise Pro-pre à prendre des photos du bien avant et après la prestation aux fins d'exécution du contrat (traçabilité qualité).
            La publication de ces photos sur la galerie publique du site ou sur les réseaux sociaux n'aura lieu <b>qu'avec le consentement écrit explicite</b> du Client (opt-in).
            Le Client peut retirer ce consentement à tout moment.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 11 — Réclamations</h2>
          <p>
            Toute réclamation doit être adressée par écrit à <a href={`mailto:${L.email}?subject=Réclamation`} className="text-[#5BA4D4]">{L.email}</a>
            {" "}dans un délai de 8 jours suivant la prestation. Pro-pre s'engage à répondre sous 5 jours ouvrés.
          </p>
          <p>
            Le Client consommateur peut également saisir la plateforme européenne de règlement en ligne des litiges :
            {" "}<a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-[#5BA4D4]">ec.europa.eu/consumers/odr</a>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 12 — Protection des données</h2>
          <p>
            Le traitement des données personnelles est décrit dans notre <Link to="/privacy" className="text-[#5BA4D4]">Politique de confidentialité</Link>, conforme au RGPD.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 13 — Force majeure</h2>
          <p>
            Pro-pre ne pourra être tenu responsable en cas d'inexécution ou de retard dû à un événement de force majeure au sens de l'article 1218 du Code civil français
            (grève, intempéries, panne technique, épidémie, événement extérieur imprévisible et irrésistible).
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">Article 14 — Droit applicable et juridiction</h2>
          <p>
            {L.applicableLaw}
          </p>
          <p>
            En cas de litige non résolu à l'amiable, le Client consommateur peut saisir, à son choix, les juridictions du lieu où il demeurait lors de la conclusion du contrat ou de la survenance du fait dommageable ({L.competentCourt}).
          </p>
          <p>
            Le Client consommateur peut également recourir gratuitement à un médiateur de la consommation ou à la plateforme européenne :
            {" "}<a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-[#5BA4D4]">ec.europa.eu/consumers/odr</a>
          </p>

          <div className="mt-10 pt-6 border-t border-slate-200 text-sm text-slate-500">
            Voir aussi : <Link to="/privacy" className="text-[#5BA4D4]">Politique de confidentialité</Link>
            {" · "}
            <Link to="/mentions-legales" className="text-[#5BA4D4]">Mentions légales</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
