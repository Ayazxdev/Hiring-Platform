"""Zynd webhook wrapper for linkedin agent.

This exposes the agent on Zynd's standard webhook endpoints.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage

from .common import parse_json_content, dump_json

load_dotenv()

# Ensure the agents_files package is importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
CLEAN_SYS = REPO_ROOT / "agents_files"
if str(CLEAN_SYS) not in sys.path:
    sys.path.insert(0, str(CLEAN_SYS))
SKILL_DIR = CLEAN_SYS / "skill_verification_agent"
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

def build_agent() -> ZyndAIAgent:
    cfg = AgentConfig(
        name="LinkedIn Agent",
        description="Parses LinkedIn profile PDFs to extract work history and verified skills.",
        capabilities={"ai": ["linkedin_parsing", "experience_extraction"], "protocols": ["http"], "services": ["fair_hiring", "linkedin_parsing"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("LINKEDIN_ZYND_PORT", "5107")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, "credentials/linkedin_vc.json")),
        config_dir=os.getenv("LINKEDIN_ZYND_CONFIG_DIR", ".agent-linkedin"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        print(f"\n[linkedin] 📬 Received Message ID: {message.message_id}")
        payload = parse_json_content(message.content)
        print(f"[linkedin] 🔍 Payload: {payload}")
        
        try:
            from skill_verification_agent.agents.linkedin_parser import LinkedInPDFParser
            parser = LinkedInPDFParser()
            
            # Replicate LinkedIn service logic for finding the path
            tmp_path = payload.get('linkedin_path') or payload.get('linkedin_url') or payload.get('pdf_path')
            
            if not tmp_path or not os.path.exists(tmp_path):
                result = {"error": f"LinkedIn PDF not found at {tmp_path}", "success": False}
                print(f"[linkedin] ⚠️ Error: PDF not found at {tmp_path}")
            else:
                print(f"[linkedin] 🚀 Parsing PDF: {os.path.basename(tmp_path)}")
                parsed = parser.parse(tmp_path)
                result = {
                    "success": True,
                    "identity": parsed.get("identity", {}),
                    "experience": parsed.get("experience", {}),
                    "skills": parsed.get("skills", {}),
                    "confidence_score": parsed.get("confidence_score", 0.0)
                }
                print(f"[linkedin] ✅ Parsing Complete for {parsed.get('identity', {}).get('name', 'Unknown')}")
        except Exception as e:
            import traceback
            print(f"[linkedin] ❌ Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "linkedin"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))
        print(f"[linkedin] 📤 Sent Result for {message.message_id}\n")

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[linkedin] Agent ID: {agent.agent_id}")
    print(f"[linkedin] Webhook URL: {agent.webhook_url}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[linkedin] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
