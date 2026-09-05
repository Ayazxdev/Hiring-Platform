"""Zynd webhook wrapper for Codeforces agent.

This exposes the agent on Zynd's standard webhook endpoints:
  - POST /webhook (async)
  - POST /webhook/sync (sync, waits for set_response)
  - GET  /health

The business logic is reused from your existing codebase (no rewrite).
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv # type: ignore
from zyndai_agent.agent import AgentConfig, ZyndAIAgent # type: ignore
from zyndai_agent.message import AgentMessage # type: ignore

try:
    from .common import parse_json_content, dump_json # type: ignore
except (ImportError, ValueError):
    # Fallback for IDE or direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from common import parse_json_content, dump_json # type: ignore

load_dotenv()

# FORCE UTF-8 for Windows console (Fix for emoji crash)
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8') # type: ignore
        sys.stderr.reconfigure(encoding='utf-8') # type: ignore
    except (AttributeError, Exception):
        pass

# Ensure the agents_files package is importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
# Note: codeforces scraper is in skill_verification_agent
SKILL_VER_DIR = REPO_ROOT / "agents_files" / "skill_verification_agent"
if str(SKILL_VER_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_VER_DIR))

def build_agent() -> ZyndAIAgent:
    cfg = AgentConfig(
        name="Codeforces Agent",
        description="Scrapes and analyzes Codeforces profiles for competitive programming evidence.",
        capabilities={"ai": ["codeforces_analysis", "evidence_extraction"], "protocols": ["http"], "services": ["fair_hiring", "codeforces_analysis"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("CODEFORCES_ZYND_PORT", "5109")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, "credentials/codeforce_vc.json")),
        config_dir=os.getenv("CODEFORCES_ZYND_CONFIG_DIR", ".agent-codeforce"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        print(f"\n[codeforces] 📬 Received Message ID: {message.message_id}")
        payload = parse_json_content(message.content)
        print(f"[codeforces] 🔍 Payload: {payload}")
        
        try:
            from scraper.codeforce_tool import analyze_codeforces_profile # type: ignore
            
            handle = payload.get('handle')
            codeforces_url = payload.get('codeforces_url')
            
            if not handle and codeforces_url:
                handle = codeforces_url.rstrip('/').split('/')[-1]
                
            if not handle:
                result = {"error": "Handle or codeforces_url required", "success": False}
                print("[codeforces] ⚠️ Error: Handle required")
            else:
                print(f"[codeforces] 🚀 Analyzing Profile: {handle}")
                # Reusing existing tool logic
                cf_data = analyze_codeforces_profile(handle)
                
                result = {
                    "success": True,
                    "handle": handle,
                    "rating": cf_data.get("rating", 0),
                    "max_rating": cf_data.get("max_rating", 0),
                    "rank": cf_data.get("rank", "Unrated"),
                    "problems_solved": cf_data.get("problems_solved", 0),
                    "top_skills": cf_data.get("top_skills", []),
                    "top_language": cf_data.get("top_language")
                }
                print(f"[codeforces] ✅ Analysis Complete for {handle}")
        except Exception as e:
            import traceback
            print(f"[codeforces] ❌ Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "codeforces"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))
        print(f"[codeforces] 📤 Sent Result for {message.message_id}\n")

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[codeforces] Agent ID: {agent.agent_id}")
    print(f"[codeforces] Webhook URL: {agent.webhook_url}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[codeforces] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
