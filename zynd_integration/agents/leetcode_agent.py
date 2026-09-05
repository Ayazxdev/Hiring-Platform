"""Zynd webhook wrapper for LeetCode agent.

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
# Note: leetcode scraper is in skill_verification_agent
SKILL_VER_DIR = REPO_ROOT / "agents_files" / "skill_verification_agent"
if str(SKILL_VER_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_VER_DIR))

def build_agent() -> ZyndAIAgent:
    cfg = AgentConfig(
        name="LeetCode Agent",
        description="Scrapes and analyzes LeetCode profiles for problem-solving evidence.",
        capabilities={"ai": ["leetcode_analysis", "evidence_extraction"], "protocols": ["http"], "services": ["fair_hiring", "leetcode_analysis"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("LEETCODE_ZYND_PORT", "5108")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, "credentials/leetcode_vc.json")),
        config_dir=os.getenv("LEETCODE_ZYND_CONFIG_DIR", ".agent-leetcode"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        print(f"\n[leetcode] 📬 Received Message ID: {message.message_id}")
        payload = parse_json_content(message.content)
        print(f"[leetcode] 🔍 Payload: {payload}")
        
        try:
            from scraper.leetcode_tool import analyze_leetcode_profile # type: ignore
            
            username = payload.get('username')
            leetcode_url = payload.get('leetcode_url')
            
            if not username and leetcode_url:
                username = leetcode_url.rstrip('/').split('/')[-1]
                
            if not username:
                result = {"error": "Username or leetcode_url required", "success": False}
                print("[leetcode] ⚠️ Error: Username required")
            else:
                print(f"[leetcode] 🚀 Analyzing Profile: {username}")
                # Reusing existing tool logic
                leetcode_data = analyze_leetcode_profile(f"https://leetcode.com/{username}")
                
                result = {
                    "success": True,
                    "username": username,
                    "total_solved": leetcode_data.get("problems_solved", 0),
                    "ranking": int(leetcode_data.get("rank", 0)) if leetcode_data.get("rank") and leetcode_data.get("rank") != "N/A" else None,
                    "level": leetcode_data.get("level"),
                    "top_skills": leetcode_data.get("top_skills", []),
                    "top_language": leetcode_data.get("top_language"),
                    "contest_rating": leetcode_data.get("contest_rating", 0)
                }
                print(f"[leetcode] ✅ Analysis Complete for {username}")
        except Exception as e:
            import traceback
            print(f"[leetcode] ❌ Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "leetcode"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))
        print(f"[leetcode] 📤 Sent Result for {message.message_id}\n")

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[leetcode] Agent ID: {agent.agent_id}")
    print(f"[leetcode] Webhook URL: {agent.webhook_url}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[leetcode] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
