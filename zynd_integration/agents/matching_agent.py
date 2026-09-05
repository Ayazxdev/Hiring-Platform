"""Zynd webhook wrapper for matching agent.

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
        name="Matching Agent",
        description="Matches verified candidate skill signals to job requirements with transparency.",
        capabilities={"ai": ["matching", "ranking", "explainability"], "protocols": ["http"], "services": ["fair_hiring", "matching"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("MATCHING_ZYND_PORT", "5101")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, os.getenv("MATCHING_ZYND_VC", "credentials/matching_vc.json"))),
        config_dir=os.getenv("MATCHING_ZYND_CONFIG_DIR", f".agent-matching"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        payload = parse_json_content(message.content)

        try:
            from matching_agent.agents.matching_agent import MatchingAgent
            agent_impl = MatchingAgent()
            
            jd = payload.get('job') or payload.get('job_description')
            candidate = payload.get('credential') or payload.get('candidate') or payload.get('candidate_profile') or payload
            
            # Use 'match' method as seen in the outline
            result = agent_impl.match(jd=jd, candidate=candidate)
        except Exception as e:
            import traceback
            print(f"[matching] Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "matching"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[matching] Agent ID: {agent.agent_id}")
    print(f"[matching] Webhook URL: {agent.webhook_url}")
    print(f"[matching] Registry URL: {agent.agent_config.registry_url}")
    print(f"[matching] Capabilities: {agent.agent_config.capabilities}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[matching] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
