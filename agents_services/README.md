# Fair Hiring Network — Agent Services

Autonomous verification microservices that inspect code quality, audit resume fraud, verify competitive coding benchmarks, detect demographic bias, and generate cryptographic skill credentials.

## Execution

### Option A: Unified Aggregator (Recommended, Port 8000)
Mounts all services under a single FastAPI instance:

```powershell
python -m uvicorn agents_services.agents_aggregator:app --host 0.0.0.0 --port 8000
```
Interactive OpenAPI documentation: `http://localhost:8000/docs`

### Option B: Standalone Multi-Port Mode
Launches each agent as an independent process on dedicated ports:

```powershell
cd agents_services
python start_all.py
```

## Agent Service Registry

| Agent | Aggregator Prefix | Standalone Port | Verification & Telemetry Scope |
| :--- | :--- | :--- | :--- |
| **Matching Agent** | `/matching` | `8001` | Multi-pillar evidence weighting, requirement scoring, and offer/interview recommendations. |
| **Bias Agent** | `/bias` | `8002` | Demographic proxy indicators, disparate impact ratio calculation, and JD bias auditing. |
| **Skill Agent** | `/skill` | `8003` | Multi-source skill ontology taxonomy matching, AST depth verification, and confidence scoring. |
| **ATS Agent** | `/ats` | `8004` | Resume PDF security scanning: prompt injection interception, `#FFFFFF` hidden white-text, and zero-point fonts. |
| **GitHub Agent** | `/github` | `8005` | Repository ownership, commit author matching, language diversity, and commit velocity analysis. |
| **LeetCode Agent** | `/leetcode` | `8006` | Contest ratings, problem solving volume, and topic mastery (DP, graph, greedy). |
| **LinkedIn Agent** | `/linkedin` | `8007` | Career tenure, verified role history, and institutional background via residential scraping. |
| **Passport Agent** | `/passport` | `8008` | Credential aggregation, SHA-256 payload hashing, and Ed25519 cryptographic signing. |
| **Codeforces Agent** | `/codeforces` | `8011` | Max rating, current rating tier (Specialist, Expert, Candidate Master), and contest submission statistics. |

## Resilience & Operational Architecture

- **Local Inference with Deterministic Fallback**: Uses local Ollama (`llama3.2`) for narrative analysis. If Ollama is offline or times out (3s limit), the system automatically defaults to deterministic ontology and regex parsing without interrupting the pipeline.
- **Anti-Bot Resilience**: Problem-solving scrapers use `curl_cffi` browser fingerprint impersonation to bypass Cloudflare challenges on LeetCode and Codeforces.
- **LinkedIn Proxy Loop**: Connects to the Bright Data LinkedIn dataset API, with graceful fallback to cached applicant profiles if quota is exceeded or offline.
