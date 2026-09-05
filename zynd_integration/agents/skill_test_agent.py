"""Zynd webhook wrapper for conditional test agent (AI Interview)."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage

from .common import parse_json_content, dump_json

load_dotenv()

# Force UTF-8 for Windows
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parents[2]

def build_agent() -> ZyndAIAgent:
    cfg = AgentConfig(
        name="Skill Test Agent",
        description="Generates and evaluates AI-driven technical tests and interviews.",
        capabilities={"ai": ["test_generation", "evaluation"], "protocols": ["http"], "services": ["fair_hiring", "skill_test"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("TEST_ZYND_PORT", "5109")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, "credentials/test_vc.json")),
        config_dir=".agent-test",
    )
    return ZyndAIAgent(agent_config=cfg)

def attach_handler(agent: ZyndAIAgent) -> None:
    # This agent wraps the logic from conditional_test_service.py
    # but for simplicity in the demo, we can just relay or implement the mock logic
    def handler(message: AgentMessage, topic: str):
        payload = parse_json_content(message.content)
        action = payload.get("action", "generate")
        
        try:
            if action == "generate":
                skills = payload.get("skills", ["Software Engineering"])
                # Mock generation for the demo logs
                result = {
                    "test_id": "ZYND-TEST-88",
                    "questions": [{"id": "q1", "text": f"Explain {s} in 3 sentences."} for s in skills[:3]],
                    "status": "generated"
                }
            else:
                result = {"score": 85, "passed": True, "feedback": "Excellent Zynd-verified performance."}
        except Exception as e:
            result = {"error": str(e)}

        agent.set_response(message.message_id, dump_json(result))

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)
    print(f"[skill-test] Agent ID: {agent.agent_id}")
    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[skill-test] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
