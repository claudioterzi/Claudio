# RRREMERGEN Setup & Deployment Guide

## Overview

RRREMERGEN is a multi-agent web app auto-composer system integrated into La Soglia (Claudio's Creative Studio). It uses:

- **Frontend**: React SPA with Framer Motion animations (integrated into La Soglia via hash routing)
- **Backend**: FastAPI server with streaming composition pipeline
- **LLM Routing**: Multi-provider support (Anthropic, OpenAI, Google, DeepSeek, Mistral)
- **Agents**: Architect → Designer → Developer → Integrator → PM (with self-debugging)

---

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend development)
- API keys for LLM providers (Anthropic, OpenAI, Google, etc.)
- Vercel account (for deployment)
- GitHub account (for app generation)

---

## Local Development Setup

### 1. Install Backend Dependencies

```bash
cd /home/user/Claudio
pip install -r rrremergen/requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file in project root:

```env
# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (GPT-4)
OPENAI_API_KEY=sk-...

# Google (Gemini)
GOOGLE_API_KEY=AIza...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# Mistral
MISTRAL_API_KEY=...

# GitHub (for app generation)
GITHUB_TOKEN=ghp_...

# Vercel (for deployment)
VERCEL_TOKEN=...
VERCEL_ORG_ID=...
VERCEL_PROJECT_ID=...
```

### 3. Start FastAPI Backend

```bash
python rrremergen/api/main.py
```

Server runs on `http://localhost:8000`

Endpoints:
- `POST /api/rrremergen/compose` - Compose new app (streaming SSE)
- `GET /health` - Provider health & availability
- `GET /models` - List available LLM models
- `POST /api/rrremergen/validate` - Validate generated code
- `POST /api/rrremergen/deploy` - Deploy to Vercel

### 4. Start Frontend Development Server

In another terminal:

```bash
cd studio/web
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

Navigate to `http://localhost:5173/#rrremergen` to access RRREMERGEN composer

---

## Production Deployment

### Vercel Deployment

1. **Backend as Serverless Function** (requires configuration)
   - Move FastAPI endpoints to `/api/rrremergen.py` Vercel function
   - Update frontend to call `/api/rrremergen` instead of local endpoint

2. **Frontend Integration**
   - Already integrated into La Soglia at `/#rrremergen`
   - Builds automatically with `npm run build`
   - Deployed to Vercel with the main La Soglia site

3. **Environment Variables**
   - Set in Vercel project settings
   - API keys for LLM providers
   - GitHub and Vercel tokens for auto-deployment

---

## Architecture

### Request Flow

```
User Input (Frontend)
    ↓
POST /api/rrremergen/compose (Streaming SSE)
    ↓
RRRemeRgenOrchestrator.compose_app()
    ├─ Architect: Requirements analysis → AppBlueprint
    ├─ Designer: UI/UX specifications
    ├─ Developer: Full-stack code generation
    ├─ Integrator: Third-party service setup
    ├─ PM: Code validation & debugging (up to 3 iterations)
    └─ Deploy: GitHub push & Vercel deployment
    ↓
Client receives SSE events with stage progress
    ↓
Completion event with GitHub repo + Vercel URL
```

### Agent Specifications

| Agent | Model | Task | Output |
|-------|-------|------|--------|
| **Architect** | Claude 3.5 Sonnet | Requirement analysis, blueprint creation | `AppBlueprint` |
| **Designer** | Gemini 2.5 Pro | UI/UX design specs | Design specifications |
| **Developer** | GPT-4 Turbo | Full-stack code generation | React + FastAPI + MongoDB |
| **Integrator** | Claude 3.5 Sonnet | API integration setup | Service configuration |
| **PM** | Claude 3.5 Sonnet | Code validation & debugging | Validation results |

---

## Testing RRREMERGEN

### Manual Testing

```bash
# Test composition endpoint
curl -X POST http://localhost:8000/api/rrremergen/compose \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a todo list app with user authentication and MongoDB"}'

# Test health check
curl http://localhost:8000/health

# Test available models
curl http://localhost:8000/models
```

### Browser Testing

1. Start frontend: `npm run dev` in `studio/web/`
2. Navigate to `http://localhost:5173/#rrremergen`
3. Enter app description (e.g., "E-commerce platform with Stripe payments")
4. Watch agents compose the app in real-time
5. Click GitHub/Vercel links when complete

---

## Troubleshooting

### "Provider not available" error
- Check `.env` file has all required API keys
- Verify API keys are valid and not rate-limited
- Check `GET /health` endpoint for provider status

### Streaming stops mid-composition
- Check FastAPI server logs for errors
- Verify network connection stability
- Try again with shorter prompt

### Generated code quality issues
- PM agent runs up to 3 debugging iterations
- Issues are logged with severity levels
- PM agent can request Developer fixes automatically

### Deployment fails
- Verify Vercel project exists and credentials are correct
- Check GitHub token has `repo` and `delete_repo` scopes
- Ensure generated code follows Vercel deployment requirements

---

## Next Steps

1. **Connect Real LLM APIs**
   - Replace placeholder responses with actual API calls
   - Implement error handling and retries
   - Add rate limiting and caching

2. **GitHub Integration**
   - Implement actual GitHub repository creation
   - Add branch protection and CI/CD setup
   - Auto-commit generated code

3. **Vercel Deployment**
   - Implement serverless deployment
   - Add preview deployments for testing
   - Set up custom domains

4. **Safety Gate Integration**
   - Add human-in-the-loop approval for generated apps
   - Implement security scanning
   - Add compliance checking

5. **Advanced Features**
   - Multi-step refinement iterations
   - Custom component library integration
   - Learning from successful compositions

---

## Project Structure

```
rrremergen/
├── api/
│   ├── main.py              # FastAPI server
│   ├── orchestrator.py       # Multi-agent coordinator
│   ├── router.py            # LLM provider routing
│   └── __init__.py
├── agents/
│   ├── architect.py          # Requirement analysis
│   ├── designer.py           # UI/UX design
│   ├── developer.py          # Code generation
│   ├── integrator.py         # Service integration
│   ├── pm.py                 # Code validation
│   └── __init__.py
├── frontend/
│   ├── RRRemeRgen.jsx        # Main React component
│   ├── RRRemeRgen.css        # Styling
│   └── __init__.py
├── requirements.txt          # Python dependencies
├── SETUP.md                  # This file
└── README.md                 # Architecture overview
```

---

## Integration with La Soglia

RRREMERGEN is accessible via La Soglia's main navigation:

1. Link: `#rrremergen` in Nav (styled with cyan gradient)
2. Route handling in `studio/web/src/App.jsx`
3. API calls to `http://api-host/api/rrremergen/compose`

When La Soglia is deployed to Vercel:
- Frontend: Served from Vercel edge network
- Backend: Can be serverless function or separate service
- Frontend + Backend communication: CORS enabled for all origins (restrict in production)

---

## Performance & Scaling

- **Streaming responses**: SSE for real-time stage updates
- **Async/await**: All I/O operations non-blocking
- **Agent parallelization**: Could parallelize independent stages (Designer, Integrator)
- **Caching**: LLM responses could be cached by similarity
- **Rate limiting**: Implement per-user/IP rate limits for production

---

## Security Considerations

- API keys stored in environment variables (never in code)
- CORS headers configured (restrict to La Soglia domain in production)
- Input validation on all endpoints
- Generated code goes through PM validation before deployment
- Vercel deployment keys secured in environment

---

For questions or issues, check `/home/user/Claudio/MEMORIA_PROGETTO.md` for project context.
