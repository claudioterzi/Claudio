# RRREMERGEN — Web App Auto-Composer (R³∞ Protocol)

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

- ⏳ Frontend component (RRRemeRgen.jsx)
- ⏳ Backend API orchestration
- ⏳ Agent implementations
- ⏳ LLM Router integration
- ⏳ Safety Gate integration

## Prossimi Step

1. Implementare RRRemeRgen.jsx frontend
2. Creare API endpoint `/api/rrremergen`
3. Implementare gli agenti specializzati
4. Integrare LLM Router
5. Testare pipeline end-to-end
