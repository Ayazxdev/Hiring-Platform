# Fair Hiring Network — Frontend Application

React 18 single-page application providing user interfaces for Candidates as well as Companies. Built with Vite, Tailwind CSS, Framer Motion, and Three.js.

## Setup & Running

### 1. Install Dependencies
```bash
cd fair-hiring-frontend
npm install
```

### 2. Development Server (Port 5173)
```bash
npm run dev
```
Application interface: `http://localhost:5173`

### 3. Production Build
```bash
npm run build
```

## Route Architecture

| Route | Component | Purpose |
| :--- | :--- | :--- |
| `/` | `LandingPage` | Platform overview, verified capabilities, and 3D hero |
| `/company` | `CompanyPage` | Company portal entry and authentication |
| `/company/dashboard` | `CompanyDashboard` | Active job listings, application counts, and role metrics |
| `/company/role-pipeline` | `CompanyRolePipeline` | Candidate pipeline stages, scoring filters, and mail-merge dispatch |
| `/company/hiring-flow` | `CompanyHiringFlow` | Multi-step job posting wizard with bias pre-audit |
| `/reviewer` | `ReviewerExperience` | Forensic fraud audit terminal (prompt injection, hidden text, git author analysis) |
| `/candidate` | `CandidatePage` | Candidate profile management and application status tracking |
| `/candidate/interview` | `ProtocallApp` | Real-time technical interview session powered by Gemini AI |
| `/passport/:id` | `PassportPage` | Verified Ed25519 cryptographic skill passport viewer |
| `/system-flow` | `SystemFlowPage` | Interactive multi-agent pipeline flow diagram |

## Environment Configuration

Configure `.env` or `.env.local` in `fair-hiring-frontend/`:

```env
VITE_API_URL=http://localhost:8012
VITE_GEMINI_API_KEY=your_gemini_api_key
VITE_ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## Troubleshooting

| Issue | Resolution |
| :--- | :--- |
| API connection errors | Ensure backend engine is running on `http://localhost:8012` |
| Port 5173 in use | Pass `--port <number>` or kill existing Vite process |
| Stale build modules | Clear cache: `rm -rf node_modules package-lock.json && npm install` |