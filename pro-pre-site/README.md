# Pro-pre Nettoyage Professionnel — Backup complet (full-source)

**Date du backup**: 2026-07-04
**Version**: Preview snapshot au moment de l'export
**Production**: https://pro-pre.com
**Entité légale**: Claudio Terzi — Entrepreneur individuel — SIRET 978 548 329 00017

---

## ⚠️ Note sur ce dépôt (recovery 2026-07-04)

Ce dossier `pro-pre-site/` a été restauré dans la repo GitHub `claudioterzi/claudio`
(branche `claude/pro-pre-site-recovery-40sdcm`) à partir du full-source backup
export d'Emergent, suite à la disparition du projet sur emergent.sh.

**Volontairement exclus de ce commit git** (contenus dans le zip original mais
pas committés ici, pour des raisons de confidentialité/RGPD) :
- `database/` — dump MongoDB avec réservations, contrats signés, transactions
  Stripe et données clients réelles. Ne doit pas être poussé dans un dépôt git,
  même privé. Le dump original reste disponible dans l'upload que tu as envoyé
  à Claude ; à restaurer directement dans un nouveau cluster MongoDB (Atlas ou
  autre) via `mongorestore`, puis à conserver hors-git (disque chiffré, cloud
  perso).
- `legal_snapshot/static_build/` — build de production déjà compilée (régénérable
  avec `yarn build`, inutile de la versionner).

## Contenu de ce dossier

```
pro-pre-site/
├── README.md                    ← Ce fichier
├── frontend/                    ← Code source React complet
│   ├── src/                     ← Tous les composants React (pages, i18n, lib, utils)
│   ├── public/                  ← Assets statiques (og-image, favicon, robots.txt, sitemap.xml)
│   ├── package.json             ← Dépendances Node.js
│   ├── tailwind.config.js       ← Config Tailwind
│   └── craco.config.js          ← Config bundler
├── backend/                     ← Code source FastAPI complet
│   ├── server.py                ← API principal (routes /api/*)
│   ├── email_service.py         ← Envoi emails Resend (magic link, notifs)
│   ├── pdf_generator.py         ← Génération contrats PDF (ReportLab)
│   ├── scripts/                 ← Scripts utilitaires (OG image, etc.)
│   └── requirements.txt         ← Dépendances Python
└── legal_snapshot/
    └── rendered_html/           ← Pages publiques rendues (Home, Privacy, CGV, Règlement, etc.)
                                    conservées comme preuve "à date certaine"
```

Aucune clé/secret réel n'est présent dans ce dossier (pas de `.env`, seulement
la liste des variables nécessaires plus bas).

## Valeur légale de ce backup

- **Copie à date certaine** des CGV, Politique de confidentialité, Mentions Légales,
  Règlement & Confiance présentés publiquement le 2026-07-04.
- **Dump complet des contrats signés** — art. L123-22 C. com FR : obligation de
  conservation 10 ans pour les documents commerciaux.
- **Log RGPD** (collection `gdpr_audit`) : trace anonymisée des demandes
  d'accès/suppression clients — utile en cas de contrôle CNIL / APD-GBA.

## Comment ré-héberger le site ailleurs

### Option 1 — Vetrina statique uniquement (le plus simple)
Uploader `legal_snapshot/static_build/` sur n'importe quel hébergeur statique :
- **Vercel** (gratuit) : `vercel --prod` dans le dossier
- **Netlify** (gratuit) : drag & drop
- **IONOS Static** : upload FTP
- **Cloudflare Pages** (gratuit)
- **AWS S3 + CloudFront**

⚠️ Attention : les fonctions dynamiques (réservations, contrats, paiements,
espace client, dashboard admin) NE FONCTIONNERONT PAS sans backend.

### Option 2 — Ré-héberger l'application complète

**A) Backend FastAPI + MongoDB**
```bash
# 1. Prérequis
sudo apt install python3.11 python3-pip

# 2. Installer
cd backend/
pip install -r requirements.txt

# 3. Configurer
cp .env.example .env
# Éditer .env avec vos vraies clés (MONGO_URL, RESEND_API_KEY, STRIPE_API_KEY, ...)

# 4. Restaurer la base MongoDB (dump conservé hors-git, voir note ci-dessus)
mongorestore --uri="<votre_MONGO_URL>" --db=<votre_DB_NAME> chemin/vers/database/<DB_NAME>/

# 5. Lancer
uvicorn server:app --host 0.0.0.0 --port 8001
```

Options d'hébergement backend :
- **Railway** (railway.app) — facile, ~5 €/mois
- **Render** (render.com) — free tier + $7/mois
- **VPS OVH / Hetzner / DigitalOcean** — 4-10 €/mois avec Docker
- **AWS ECS / Google Cloud Run** — pay-per-use

MongoDB hébergé :
- **MongoDB Atlas** (mongodb.com) — Free tier 512 MB, largement suffisant

**B) Frontend React**
```bash
cd frontend/
yarn install
cp .env.example .env
# Éditer .env avec l'URL de votre backend
yarn build
# Uploader `build/` sur Vercel/Netlify/Cloudflare Pages
```

## Configuration des variables sensibles

Après ré-hébergement, vous devez recréer/récupérer :

| Variable                  | Où l'obtenir                                     |
|---------------------------|--------------------------------------------------|
| `MONGO_URL`               | MongoDB Atlas → Cluster → Connect                 |
| `RESEND_API_KEY`          | https://resend.com/api-keys                       |
| `STRIPE_API_KEY`          | https://dashboard.stripe.com/apikeys              |
| `STRIPE_WEBHOOK_SECRET`   | Dashboard Stripe → Developers → Webhooks          |
| `EMERGENT_LLM_KEY`        | https://app.emergent.sh (Profile → Universal Key) |
| `MAGIC_LINK_SECRET`       | Générer : `python -c "import secrets; print(secrets.token_urlsafe(48))"` |

## Domaine

Le domaine `pro-pre.com` est enregistré chez **IONOS**. Pour le pointer vers
un nouveau serveur, mettre à jour les enregistrements DNS de type **A** dans
le panneau IONOS (voir la doc de votre nouvel hébergeur pour les IPs).

## Contact

Claudio Terzi — Terziclaudio@gmail.com — +33 6 74 93 20 00

---

**Ce backup est propriété exclusive de Claudio Terzi (SIRET 978 548 329 00017).**
