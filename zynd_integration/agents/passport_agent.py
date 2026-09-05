"""Zynd webhook wrapper for passport agent.

This exposes the agent on Zynd's standard webhook endpoints:
  - POST /webhook (async)
  - POST /webhook/sync (sync, waits for set_response)
  - GET  /health

The business logic is reused from your existing codebase (no rewrite).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage

from .common import parse_json_content, dump_json

load_dotenv()

# FORCE UTF-8 for Windows console (Fix for emoji crash)
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

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
        name="Passport Agent",
        description="Issues/returns verifiable hiring passport payloads (credential packaging for downstream trust).",
        capabilities={"ai": ["credential_issuing", "auditability"], "protocols": ["http"], "services": ["fair_hiring", "passport"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("PASSPORT_ZYND_PORT", "5105")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, os.getenv("PASSPORT_ZYND_VC", "credentials/passport_vc.json"))),
        config_dir=os.getenv("PASSPORT_ZYND_CONFIG_DIR", f".agent-passport"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        payload = parse_json_content(message.content)

        try:
            from passport_agent.agents.passport_agent import PassportAgent
            agent_impl = PassportAgent()

            # Extract credential payload attributes handling either flattened or nested structure
            credential_data = {
                "verified_skills": payload.get("verified_skills") or payload.get("credential_data", {}).get("verified_skills", []),
                "skill_confidence": payload.get("skill_confidence") or payload.get("credential_data", {}).get("skill_confidence"),
                "match_score": payload.get("match_score"),
                "application_id": payload.get("application_id"),
                "candidate": payload.get("candidate"),
                "job_id": payload.get("job_id"),
            }
            # Merge other top-level payload fields into credential_data if they are not already there
            # and are not 'credential_data' itself.
            for key, value in payload.items():
                if key not in credential_data and key != "credential_data":
                    credential_data[key] = value

            result = agent_impl.issue_passport(credential_data)
        except Exception as e:
            result = {"error": str(e), "agent": "passport"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[passport] Agent ID: {agent.agent_id}")
    print(f"[passport] Webhook URL: {agent.webhook_url}")
    print(f"[passport] Registry URL: {agent.agent_config.registry_url}")
    print(f"[passport] Capabilities: {agent.agent_config.capabilities}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[passport] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
