"""Zynd webhook wrapper for bias agent.

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

# FORCE UTF-8 for Windows console to prevent crash on emoji/bullets
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass # Python < 3.7

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
        name="Bias Agent",
        description="Detects bias signals in hiring decisions and produces an explainable bias report.",
        capabilities={"ai": ["bias_detection", "explainability"], "protocols": ["http"], "services": ["fair_hiring", "bias_detection"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("BIAS_ZYND_PORT", "5102")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, os.getenv("BIAS_ZYND_VC", "credentials/bias_vc.json"))),
        config_dir=os.getenv("BIAS_ZYND_CONFIG_DIR", f".agent-bias"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        payload = parse_json_content(message.content)

        try:
            from bias_detection_agent.agents.bias_detection_agent import BiasDetectionAgent
            agent_impl = BiasDetectionAgent()
            result = agent_impl.run_analysis(credential_input=payload.get('credential') or payload, mode=payload.get('mode','realtime'))
        except Exception as e:
            result = {"error": str(e), "agent": "bias"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[bias] Agent ID: {agent.agent_id}")
    print(f"[bias] Webhook URL: {agent.webhook_url}")
    print(f"[bias] Registry URL: {agent.agent_config.registry_url}")
    print(f"[bias] Capabilities: {agent.agent_config.capabilities}")

    # Graceful shutdown on SIGINT/SIGTERM
    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[bias] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
