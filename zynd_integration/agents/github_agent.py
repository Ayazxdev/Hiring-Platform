"""Zynd webhook wrapper for github agent.

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
from dotenv import load_dotenv
from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage

from .common import parse_json_content, dump_json

load_dotenv()

# Ensure the agents_files package is importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
# Note: github scraper is in skill_verification_agent
SKILL_VER_DIR = REPO_ROOT / "agents_files" / "skill_verification_agent"
if str(SKILL_VER_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_VER_DIR))

def build_agent() -> ZyndAIAgent:
    cfg = AgentConfig(
        name="GitHub Agent",
        description="Scrapes and analyzes GitHub profiles for developer technical evidence.",
        capabilities={"ai": ["github_analysis", "evidence_extraction"], "protocols": ["http"], "services": ["fair_hiring", "github_analysis"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("GITHUB_ZYND_PORT", "5106")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, "credentials/github_vc.json")),
        config_dir=os.getenv("GITHUB_ZYND_CONFIG_DIR", ".agent-github"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        print(f"\n[github] 📬 Received Message ID: {message.message_id}")
        payload = parse_json_content(message.content)
        print(f"[github] 🔍 Payload: {payload}")
        start_time = time.time()
        
        try:
            from scraper.github_api import GitHubAPIClient
            # Logic from github_service.py
            github_url = payload.get('github_url', '')
            
            # Simple extract_username inline to avoid dependencies
            url = github_url.replace('https://', '').replace('http://', '').replace('github.com/', '').rstrip('/')
            username = url.split('/')[0] if url else None
            
            if not username:
                result = {"error": "Invalid GitHub URL", "success": False}
                print("[github] ⚠️ Error: Invalid URL or username")
            else:
                print(f"[github] 🚀 Analyzing Profile: {username}")
                token = os.getenv("GITHUB_PAT") or os.getenv("GITHUB_TOKEN")
                client = GitHubAPIClient(token=token)
                
                # Replicate core analysis profile call pattern for wrapper
                user = client.get_user_profile(username)
                if not user:
                    result = {"error": f"User not found: {username}", "success": False}
                    print(f"[github] ⚠️ User not found: {username}")
                else:
                    repos = client.get_user_repos(username, max_repos=20)
                    languages = client.aggregate_languages(username, repos)
                    credibility = client.calculate_credibility_score(user)
                    best_repos = client.select_best_repositories(username, repos, top_n=3)
                    
                    result = {
                        "success": True,
                        "username": username,
                        "profile": user,
                        "credibility_signal": {
                            "score": credibility.get("credibility_score", 0),
                            "is_verified": credibility.get("credibility_score", 0) >= 50
                        },
                        "skill_signal": {
                            "primary_language": languages.get("primary_language"),
                            "verified_languages": languages.get("verified_languages", []),
                            "best_repositories": best_repos.get("best_repositories", [])
                        }
                    }
                    print(f"[github] ✅ Analysis Complete for {username}")
        except Exception as e:
            import traceback
            print(f"[github] ❌ Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "github"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))
        print(f"[github] 📤 Sent Result for {message.message_id}\n")

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[github] Agent ID: {agent.agent_id}")
    print(f"[github] Webhook URL: {agent.webhook_url}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[github] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
