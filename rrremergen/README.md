# RRREMERGEN — Web App Auto-Composer (R³∞ Protocol)

> Aggiornamento verificato 14/10/2026: leggere [VERIFICA_2026-10-14.md](VERIFICA_2026-10-14.md) per il flusso locale corretto, i test e i limiti. Le descrizioni di deployment qui sotto sono documentazione storica: il risultato corrente è un archivio di sorgenti, senza pubblicazione automatica.

Sistema autonomo per la composizione e deployment di applicazioni web.
Replica di Emergent con protocollo Claudio (R³∞) e routing multi-provider LLM.

## Architettura

```
┌─────────────────────────────────────────────┐
│     RRREMERGEN INTERFACE (React/Vite)      │
│  - Prompt input + natural language          │
│  - Live preview builder                     │
│  - Deployment + GitHub sync                 │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│    MULTI-AGENT ORCHESTRATION (Backend)     │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐   │
│  │Architect│→ │Designer │→ │Developer │   │
│  └─────────┘  └─────────┘  └──────────┘   │
│       ↓            ↓             ↓          │
│    Blueprint   UI Specs    Code Gen       │
│                                            │
│  ┌─────────┐  ┌───────────────────────┐  │
│  │Integration→ │ PM (Validation Loop)  │  │
│  └─────────┘  └───────────────────────┘  │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│    LLM ROUTER (Multi-Provider)             │
│  Anthropic → OpenAI → Gemini → DeepSeek   │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│    GENERATED APP (React + FastAPI)         │
│  - React/Next.js frontend                  │
│  - FastAPI backend with auth               │
│  - MongoDB database                        │
│  - Deployed on Vercel                      │
└─────────────────────────────────────────────┘
```

## Components

- **`agents/`** — Specialized agent implementations
  - `architect.py` — App blueprint generation
  - `designer.py` — UI/UX specifications
  - `developer.py` — Code generation (React + FastAPI + MongoDB)
  - `integrator.py` — Third-party service connections
  - `pm.py` — Validation and self-debugging loop

- **`api/`** — Backend API
  - `orchestrator.py` — Coordinates agent pipeline
  - `router.py` — LLM selection and fallback
  - `deployment.py` — GitHub push + Vercel deploy

- **`frontend/`** — Web interface (RRRemeRgen.jsx)
  - Prompt composition interface
  - Live preview and editing
  - Deployment controls

## Flusso Operativo

1. Utente inserisce prompt naturale in `/rrremergen`
2. Architect analizza → genera blueprint tecnico
3. Designer crea specazioni UI/UX
4. Developer genera codice (React + FastAPI + MongoDB)
5. Integration connette servizi terzi (Stripe, Slack, ecc.)
6. PM valida vs. requisiti → triggera self-debugging se necessario
7. Safety Gate approva la modifica
8. Deploy automatico su Vercel + push a GitHub

## Status

- ✅ Frontend component (RRRemeRgen.jsx) — Complete with Framer Motion animations
- ✅ Backend API orchestration (FastAPI server with streaming)
- ✅ Agent implementations (all 5 agents: Architect, Designer, Developer, Integrator, PM)
- ✅ LLM Router integration (multi-provider support)
- ✅ Frontend integration into La Soglia (hash routing #rrremergen)
- ✅ Nav link styling (gradient + glow effect)
- ⏳ Real LLM API connections (placeholders in place)
- ⏳ GitHub app generation + auto-push
- ⏳ Vercel deployment automation
- ⏳ Safety Gate approval workflow

## Prossimi Step

1. **Connect Real LLM APIs** — Replace placeholder implementations with actual API calls
2. **GitHub Integration** — Implement repository creation and code push
3. **Vercel Deployment** — Automate Vercel deployment with generated app
4. **Safety Gate** — Add human approval workflow before deployment
5. **Testing & Refinement** — End-to-end testing and UX optimization

## Quickstart

See `SETUP.md` for detailed setup and deployment instructions.

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Add your API keys

# Start backend
python api/main.py

# In another terminal, start frontend
cd studio/web && npm run dev

# Navigate to http://localhost:5173/#rrremergen
```
