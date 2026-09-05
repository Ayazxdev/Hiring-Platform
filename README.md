# Fair Hiring Network (FHN)

> Proof-of-work hiring. Less resume theater, more actual proof.

FHN ingests real developer evidence across GitHub, LeetCode, Codeforces, and LinkedIn, cross-examines resumes for fraud/prompt-injections, strips pedigree bias, and mints cryptographically signed Ed25519 skill passports. Zero paid cloud dependencies required to run locally.

Detailed architectural deep-dives and schemas live in [backend/README.md](backend/README.md) and [agents_services/README.md](agents_services/README.md).

---

## Features

- **Code & Velocity (GitHub):** Scans commit frequency, repo ownership, language depth, and framework dependencies.
- **Problem Solving (LeetCode & Codeforces):** Direct contest ratings, problem counts, and algorithmic tags (DP, greedy, graphs).
- **Career Reality (LinkedIn):** Real tenure, verified company roles, and portfolio proof via residential proxies.
- **Fraud & Prompt Injection Defense (ATS Guard):** Detects white text, invisible characters, system prompt injection attacks, and AI-generated resumes.
- **Human-in-the-Loop Forensic Review:** Escalates flagged anomalies (prompt injections, hidden text, author mismatches, bias loop deadlocks) to an isolated reviewer terminal with live profile handles and OCR resume audit.
- **Anti-Bias Filtering:** Eliminates pedigree gatekeeping, gendered phrasing, and demographic markers before matching.
- **Tamper-Proof Passports:** Issues signed Ed25519 portable JSON credentials.

---

## Stack

- **Core & Backend:** Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL, asyncpg, Ed25519 (`cryptography`)
- **Agents:** 10 microservices mounted under a single aggregator or routed via the Zynd protocol
- **Inference:** Local Ollama (`llama3.2` / `llama3.1`) with deterministic regex/heuristic failover
- **Frontend:** React 18, Vite, Tailwind CSS, Framer Motion

---

## Setup (The Fast Way)

### 1. Clone & Dependencies

```bash
# Clone
git clone https://github.com/your-username/Fair_Hiring_Network.git
cd Fair_Hiring_Network

# Virtual environment
python -m venv .venv

# Activate (.venv)
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install all dependencies (backend + all agents)
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Set your local PostgreSQL URL in `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/fhn
UNIFIED_AGENTS_URL=http://localhost:8000
USE_ZYND=0
```

Generate your Ed25519 signing keys with this one-liner:
```bash
python -c "from cryptography.hazmat.primitives.asymmetric import ed25519; from cryptography.hazmat.primitives import serialization; k = ed25519.Ed25519PrivateKey.generate(); print('PASSPORT_SIGNING_PRIVATE_KEY=' + k.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()).hex()); print('PASSPORT_SIGNING_PUBLIC_KEY=' + k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex())"
```
Copy the printed keys into `PASSPORT_SIGNING_PRIVATE_KEY` and `PASSPORT_SIGNING_PUBLIC_KEY` in your `.env`.

### 3. Spin Up the 3 Services

Open 3 terminals (with `.venv` activated):

**Terminal 1 — Agents Aggregator (Port 8000):**
```powershell
# From project root:
.\.venv\Scripts\Activate.ps1
python -m uvicorn agents_services.agents_aggregator:app --host 0.0.0.0 --port 8000
```
Swagger UI: `http://localhost:8000/docs`

**Terminal 2 — Backend Engine (Port 8012):**
```powershell
# Windows PowerShell (from project root):
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="backend;."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload

# Linux / macOS (from project root):
source .venv/bin/activate
export PYTHONPATH="backend:."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8012 --reload
```
Swagger UI: `http://localhost:8012/docs`

**Terminal 3 — Frontend (Port 5173):**
```bash
cd fair-hiring-frontend
npm install
npm run dev
```
App lives at `http://localhost:5173`.

---

## Tips & Gotchas

A few practical things to know so you never hit a weird bottleneck:

1. **GitHub API Rate Limits:**
   - Unauthenticated calls to GitHub are capped at 60 requests/hour by IP address. If you're testing multiple candidates, GitHub will throw HTTP 403.
   - **Fix:** Add a free GitHub token in `.env`:
     ```env
     GITHUB_PAT=ghp_yourPersonalAccessTokenHere
     ```
     This bumps your limit to 5,000 req/hr and lets the scraper inspect deeper dependencies and frameworks.

2. **LinkedIn Scraping & Bright Data:**
   - LinkedIn aggressively blocks raw scrapers. We hooked up the Bright Data LinkedIn Scraper API.
   - **Free Loophole:** Bright Data offers a 5,000 free record credit tier for developers. Add these to `.env`:
     ```env
     BRIGHT_DATA_API_KEY=your_key_here
     BRIGHT_DATA_DATASET_ID=gd_l1viktl72bvl7bjuj0
     ```
   - If left empty or offline, the system automatically falls back to an internal resilient profile so the evaluation pipeline never breaks.

3. **Handles vs. URLs:**
   - For Codeforces and LeetCode, feel free to enter either the full profile link (e.g. `https://codeforces.com/profile/denji123`, `https://leetcode.com/u/cherishjain01/`) or just the raw handle (`denji123`, `cherishjain01`). The engine normalizes both.
   - Cloudflare anti-bot checks are bypassed out-of-the-box using `curl_cffi` browser impersonation.

4. **Tesseract OCR (Optional for Image Resumes):**
   - Standard text PDFs are parsed natively via PDFMiner.
   - If candidates submit image-based or scanned PDFs, `pytesseract` handles optical character recognition.
   - If you want local OCR enabled, install the Tesseract binary:
     - **Windows:** `winget install UB-Mannheim.TesseractOCR` (default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
     - **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
     - **macOS:** `brew install tesseract`

5. **Local Ollama / Offline Fallback:**
   - If Ollama is running (`ollama run llama3.2`), it handles rich narrative extraction.
   - If Ollama is offline or slow, the dual client connection times out in 3 seconds and automatically falls back to deterministic regex and ontology scanning. No stuck processes, ever.

6. **Port Already in Use (`WinError 10048` or `WinError 10013`):**
   - If a port is already taken by a previous background terminal or session, free it in one line:
     ```powershell
     # Free Port 8000:
     Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force
     
     # Free Port 8012:
     Stop-Process -Id (Get-NetTCPConnection -LocalPort 8012).OwningProcess -Force
     ```

---

## Verification Test

Want to make sure everything is humming? Run the end-to-end suite:

```bash
python Test/e2e_test.py
```

---

## License

Distributed under the [MIT License](LICENSE).

*Go build something fair.*
