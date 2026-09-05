# pyright: reportMissingImports=false
"""Zynd webhook wrapper for ats agent.

This exposes the agent on Zynd's standard webhook endpoints:
  - POST /webhook (async)
  - POST /webhook/sync (sync, waits for set_response)
  - GET  /health

The business logic is reused from your existing codebase (no rewrite).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv # type: ignore
from zyndai_agent.agent import AgentConfig, ZyndAIAgent # type: ignore
from zyndai_agent.message import AgentMessage # type: ignore

from .common import parse_json_content, dump_json # type: ignore

load_dotenv()

# 2026 Fix: Force UTF-8 encoding for stdout/stderr on Windows to prevent charmap errors
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8') # type: ignore
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8') # type: ignore

# Ensure the agents_files package is importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
CLEAN_SYS = REPO_ROOT / "agents_files"
if str(CLEAN_SYS) not in sys.path:
    sys.path.insert(0, str(CLEAN_SYS))
# Some modules expect skill_verification_agent on path for utils imports
SKILL_DIR = CLEAN_SYS / "skill_verification_agent"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

def build_agent() -> ZyndAIAgent:
    cfg = AgentConfig(
        name="Ats Agent",
        description="Runs ATS-style checks (fraud/blacklist/policy gating) and produces a transparent pass/fail decision.",
        capabilities={"ai": ["ats_screening", "policy_checks"], "protocols": ["http"], "services": ["fair_hiring", "ats"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("ATS_ZYND_PORT", "5104")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, os.getenv("ATS_ZYND_VC", "credentials/ats_vc.json"))),
        config_dir=os.getenv("ATS_ZYND_CONFIG_DIR", f".agent-ats"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        payload = parse_json_content(message.content)

        try:
            resume_path = payload.get("resume_path")
            resume_text = payload.get("resume_text")
            application_id = payload.get("application_id")
            
            if not resume_path and not resume_text:
                result = {"error": "Missing resume_path AND resume_text in payload", "agent": "ats"}
            else:
                from skill_verification_agent.agents.ats_guard import run_ats_guard # type: ignore
                from skill_verification_agent.agents.ats import ATSEvidenceAgent # type: ignore
                
                # Step 1: Run Security Guard
                guard_result = {}
                if resume_path:
                    guard_result = run_ats_guard(resume_path)
                
                # Fast-fail if guard rejected
                status = guard_result.get("security_status", "OK")
                action = "BLACKLIST" if status == "REJECTED" else ("NEEDS_REVIEW" if status == "REVIEW" else status)
                
                # Step 2: Run Evidence Extraction
                # In Demo/Local mode, we always try to extract skills even if flagged, 
                # so the user can see what the AI found (transparency).
                ats_impl = ATSEvidenceAgent(llm=None)
                extraction_result = ats_impl.extract_evidence(
                    pdf_path=resume_path,
                    resume_text=resume_text,
                    evaluation_id=str(application_id) if application_id else None
                )
                
                # Merge Results
                flags_list = guard_result.get("flags") or []
                result = {
                    "success": True,
                    "action": action,
                    "trust_score": guard_result.get("trust_score", 100),
                    "flags": [f.get("type", "") for f in flags_list if isinstance(f, dict)],
                    "evidence": extraction_result,
                    "skills": extraction_result.get("skills", []),
                    "experience": extraction_result.get("experience", []),
                    "identity": extraction_result.get("identity", {})
                }
                skills_list = result.get('skills') or []
                print(f"[ats-debug] Extraction complete. Skills found: {len(skills_list)}") # type: ignore
                if skills_list:
                    print(f"[ats-debug] First 3 skills: {skills_list[:3]}") # type: ignore
        except Exception as e:
            import traceback
            print(f"[ats] Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "ats"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[ats] Agent ID: {agent.agent_id}")
    print(f"[ats] Webhook URL: {agent.webhook_url}")
    print(f"[ats] Registry URL: {agent.agent_config.registry_url}")
    print(f"[ats] Capabilities: {agent.agent_config.capabilities}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[ats] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
