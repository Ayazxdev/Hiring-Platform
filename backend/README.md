# Fair Hiring Network — Backend Engine

FastAPI backend orchestrating candidate applications, PostgreSQL database persistence, and multi-agent skill verification pipelines.

## Architecture & Data Flow

```
Frontend (Port 5173) / API Clients
              │
              ▼
    FastAPI Core (Port 8012)
    ├── Routers: /auth, /job, /candidate, /company, /pipeline, /passport
    └── Pipeline Orchestrator (10-stage evaluation engine)
              │
              ├─► Unified Agent Aggregator (Port 8000)
              │   ├── ATS Fraud Guard (anti-prompt injection, hidden text)
              │   ├── GitHub / LeetCode / Codeforces Scrapers
              │   ├── Skill Ontology & AST Depth Verifier
              │   ├── Demographic Bias Auditor
              │   └── Ed25519 Cryptographic Passport Signer
              │
              └─► PostgreSQL (Database Storage via SQLAlchemy + asyncpg)
```

## Setup & Running

### 1. Initialize Database Schema
From the project root with your virtual environment activated:
```powershell
python Test/init_db.py
```

### 2. Start Backend Server (Port 8012)

**Windows PowerShell:**
```powershell
$env:PYTHONPATH="backend;."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload
```

**Linux / macOS:**
```bash
export PYTHONPATH="backend:."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload
```

- API Base: `http://localhost:8012`
- Interactive Swagger UI: `http://localhost:8012/docs`
- Health Endpoint: `http://localhost:8012/health`

## Router Architecture

All routes are mounted at the root prefix:

| Prefix | Primary Handlers | Purpose |
| :--- | :--- | :--- |
| `/auth` | `/candidate/signup`, `/company/signup`, `/candidate/login`, `/company/login` | Authentication and JWT session tokens |
| `/job` | `GET /`, `POST /`, `GET /{id}` | Job postings and skill requirements |
| `/candidate` | `POST /apply`, `GET /{anon_id}/applications`, `GET /{anon_id}/stats` | Candidate submission, anonymization, and tracking |
| `/company` | `GET /{id}/role-pipeline`, `GET /{id}/review-queue`, `POST /{id}/review-queue/{case_id}/action` | Role management, candidate review, and company-isolated fraud queue |
| `/pipeline` | `POST /run`, `GET /status/{app_id}` | Multi-agent application evaluation trigger and status polling |
| `/passport` | `GET /{anon_id}`, `POST /verify` | Cryptographic Ed25519 credential passport retrieval and signature validation |

## Multi-Tenant Company Isolation

Company access to review cases is strictly isolated by job ownership in the database:
- `GET /company/{company_id}/review-queue` performs an inner join on `Job.company_id == company_id`.
- `POST /company/{company_id}/review-queue/{case_id}/action` enforces `Job.company_id == company_id`, rejecting unauthorized reviews with `404 Not Found`.

## Key Environment Variables

Configured in `.env`:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:password@localhost:5432/fhn` |
| `BACKEND_PORT` | Backend listener port | `8012` |
| `UNIFIED_AGENTS_URL` | URL of the Agent Aggregator service | `http://localhost:8000` |
| `USE_ZYND` | Toggle Zynd protocol routing vs direct aggregator | `0` (direct local aggregator) |
| `PASSPORT_SIGNING_PRIVATE_KEY` | Hex-encoded Ed25519 private key for signing passports | Generated |
| `PASSPORT_SIGNING_PUBLIC_KEY` | Hex-encoded Ed25519 public key for passport verification | Generated |
| `LLM_BACKEND` | Inference provider (`ollama`, `openai`, `gemini`) | `ollama` |

## Automated Verification Suite

Run the end-to-end test against the running services:
```bash
python Test/e2e_test.py
```