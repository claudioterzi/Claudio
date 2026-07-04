import React from "react";
import { Link } from "react-router-dom";
import { LEGAL_INFO } from "@/lib/legal";
import { Shield, Mail } from "lucide-react";

const L = LEGAL_INFO;

export default function Privacy() {
  return (
    <div className="section">
      <div className="container-narrow max-w-3xl" data-testid="privacy-page">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#5BA4D4]/10 text-[#5BA4D4]">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-[#5BA4D4] font-semibold">Pro-pre</p>
            <h1 className="text-3xl sm:text-4xl font-semibold text-navy">Politique de confidentialité</h1>
          </div>
        </div>

        <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
          <p className="text-sm text-slate-500 italic">
            Ce document est disponible uniquement en français, langue officielle de l'entreprise Pro-pre.
            <br />
            Dernière mise à jour : <b>{L.lastUpdate}</b>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">1. Responsable du traitement</h2>
          <p>
            Le responsable du traitement des données personnelles collectées via www.pro-pre.com et www.pro-pre.fr est :
          </p>
          <ul>
            <li><b>{L.entityName}</b> — {L.legalStatus}</li>
            <li>Adresse : {L.address}</li>
            <li>Email : <a href={`mailto:${L.email}`} className="text-[#5BA4D4]">{L.email}</a></li>
            <li>Téléphone : <a href={`tel:${L.phone.replace(/\s/g,'')}`} className="text-[#5BA4D4]">{L.phone}</a></li>
            <li>Numéro d'entreprise (TVA) : {L.vat}</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">2. Données que nous collectons</h2>
          <p>Dans le cadre de notre service de nettoyage textile professionnel, nous collectons :</p>
          <ul>
            <li><b>Données d'identification</b> : nom, prénom, email, téléphone</li>
            <li><b>Données de localisation</b> : adresse postale complète du domicile (pour la prestation à domicile)</li>
            <li><b>Contenu utilisateur</b> : photos avant/après du bien traité, description libre de la zone à nettoyer</li>
            <li><b>Signature électronique</b> : nom saisi comme signature du contrat "Défi de la Bande"</li>
            <li><b>Données de facturation</b> : historique des services, prix payés (via Stripe qui traite les données de carte)</li>
            <li><b>Données techniques</b> : adresse IP, cookies de session (techniques uniquement), préférence de langue</li>
            <li><b>Communications</b> : messages échangés par email, chat, WhatsApp</li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">3. Finalités et bases juridiques</h2>
          <table className="w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
            <thead className="bg-slate-50">
              <tr>
                <th className="p-3 text-left">Finalité</th>
                <th className="p-3 text-left">Base juridique (art. 6 RGPD)</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-slate-100"><td className="p-3">Exécution du contrat de nettoyage</td><td className="p-3">Contrat (art. 6.1.b)</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Envoi de confirmations et rappels par email</td><td className="p-3">Contrat + intérêt légitime</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Traitement du paiement (Stripe)</td><td className="p-3">Contrat</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Génération et archivage du contrat PDF</td><td className="p-3">Obligation légale (10 ans)</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Publication des photos avant/après en galerie</td><td className="p-3">Consentement explicite (opt-in)</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Envoi de newsletters / promotions</td><td className="p-3">Consentement (opt-in)</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Amélioration du service, statistiques anonymes</td><td className="p-3">Intérêt légitime</td></tr>
              <tr className="border-t border-slate-100"><td className="p-3">Défense en cas de litige</td><td className="p-3">Intérêt légitime</td></tr>
            </tbody>
          </table>

          <h2 className="text-2xl font-semibold text-navy mt-8">4. Durée de conservation</h2>
          <ul>
            <li>Données de réservation : <b>{L.retentionBookings}</b></li>
            <li>Contrats signés (PDF) : <b>{L.retentionContracts}</b></li>
            <li>Photos avant/après : <b>{L.retentionPhotos}</b></li>
            <li>Sessions de connexion : <b>{L.retentionSessions}</b></li>
            <li>Logs techniques : <b>{L.retentionLogs}</b></li>
          </ul>

          <h2 className="text-2xl font-semibold text-navy mt-8">5. Sous-traitants (destinataires)</h2>
          <p>Nous partageons certaines données avec les sous-traitants suivants, tous liés par un accord de traitement (DPA) et localisés en UE ou couverts par des clauses contractuelles types (SCC) :</p>
          <ul>
            {L.subProcessors.map((s) => (
              <li key={s.name}>
                <b>{s.name}</b> — {s.purpose} ({s.country}) —
                {" "}<a href={s.url} target="_blank" rel="noopener noreferrer" className="text-[#5BA4D4]">Politique</a>
              </li>
            ))}
          </ul>
          <p><b>Nous ne vendons pas vos données à des tiers.</b></p>

          <h2 className="text-2xl font-semibold text-navy mt-8">6. Vos droits</h2>
          <p>Conformément au RGPD (arts. 15 à 22), vous disposez des droits suivants :</p>
          <ul>
            <li><b>Accès</b> à vos données personnelles</li>
            <li><b>Rectification</b> des données inexactes</li>
            <li><b>Effacement</b> (droit à l'oubli)</li>
            <li><b>Limitation</b> du traitement</li>
            <li><b>Portabilité</b> de vos données (format machine)</li>
            <li><b>Opposition</b> au traitement fondé sur l'intérêt légitime</li>
            <li><b>Retrait du consentement</b> à tout moment (newsletter, galerie)</li>
            <li>Droit d'introduire une <b>réclamation auprès d'une autorité de contrôle</b> :
              {" "}<a href={L.dpaFrance.url} target="_blank" rel="noopener noreferrer" className="text-[#5BA4D4]">{L.dpaFrance.name}</a>
              {" "}(autorité de rattachement du responsable de traitement, situé en France)
              {" "}— ou l'<a href={L.dpaBelgium.url} target="_blank" rel="noopener noreferrer" className="text-[#5BA4D4]">{L.dpaBelgium.name}</a>
              {" "}pour les clients résidant en Belgique (art. 77 RGPD).
            </li>
          </ul>
          <p>
            Pour exercer vos droits, contactez-nous à <a href={`mailto:${L.privacyEmail}?subject=Demande RGPD`} className="text-[#5BA4D4]">{L.privacyEmail}</a>
            {" "}ou utilisez le bouton <b>"Supprimer mes données"</b> depuis votre espace personnel.
          </p>
          <p className="mt-4">
            <Link to="/mon-espace" className="btn-primary inline-flex">
              <Mail className="h-4 w-4" /> Accéder à mon espace
            </Link>
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">7. Cookies</h2>
          <p>
            Le site utilise uniquement des <b>cookies strictement nécessaires</b> au fonctionnement (session d'authentification, préférence de langue).
            Aucun cookie de tracking marketing ni d'analyse tiers (type Google Analytics, Facebook Pixel) n'est utilisé actuellement.
            Ces cookies techniques sont exemptés de consentement conformément à la Directive ePrivacy.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">8. Sécurité</h2>
          <p>
            Nous mettons en œuvre les mesures techniques et organisationnelles appropriées : chiffrement HTTPS/TLS, cookies HTTPOnly, séparation des bases de données, accès administrateur limité et journalisé, sauvegardes chiffrées.
            En cas de violation de données susceptible d'entraîner un risque élevé pour vos droits, nous vous en informerons dans les 72 heures conformément à l'article 34 RGPD.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">9. Modifications</h2>
          <p>
            Cette politique peut être mise à jour pour refléter des changements réglementaires ou opérationnels.
            La date de dernière mise à jour figure en haut du document.
            En cas de modification substantielle, vous en serez informé par email.
          </p>

          <h2 className="text-2xl font-semibold text-navy mt-8">10. Contact</h2>
          <p>
            Pour toute question relative à cette politique ou au traitement de vos données :
            <br />
            <b>{L.entityName}</b>
            <br />
            {L.address}
            <br />
            Email : <a href={`mailto:${L.privacyEmail}`} className="text-[#5BA4D4]">{L.privacyEmail}</a>
            <br />
            Tél : <a href={`tel:${L.phone.replace(/\s/g,'')}`} className="text-[#5BA4D4]">{L.phone}</a>
          </p>

          <div className="mt-10 pt-6 border-t border-slate-200 text-sm text-slate-500">
            Voir aussi : <Link to="/mentions-legales" className="text-[#5BA4D4]">Mentions légales</Link>
            {" · "}
            <Link to="/cgv" className="text-[#5BA4D4]">Conditions générales de vente</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
