"""Zynd webhook wrapper for skill agent.

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
        name="Skill Agent",
        description="Verifies developer skills from evidence and produces structured skill signals and confidence.",
        capabilities={"ai": ["skill_verification", "evidence_scoring"], "protocols": ["http"], "services": ["fair_hiring", "skill_verification"]},
        webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
        webhook_port=int(os.getenv("SKILL_ZYND_PORT", "5103")),
        registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
        api_key=os.getenv("ZYND_API_KEY"),
        identity_credential_path=os.path.abspath(os.path.join(REPO_ROOT, os.getenv("SKILL_ZYND_VC", "credentials/skill_vc.json"))),
        config_dir=os.getenv("SKILL_ZYND_CONFIG_DIR", f".agent-skill"),
    )

    agent = ZyndAIAgent(agent_config=cfg)
    return agent

def attach_handler(agent: ZyndAIAgent) -> None:
    def handler(message: AgentMessage, topic: str):
        payload = parse_json_content(message.content)

        try:
            from skill_verification_agent.agents.evidence_graph_builder import EvidenceGraphBuilder
            from skill_verification_agent.agents.skill_verification_agent_v2 import SkillVerificationAgentV2
            
            # Step 1: Build Evidence Graph
            builder = EvidenceGraphBuilder()
            evidence = payload.get('evidence') or payload
            
            # Helper to get case-insensitive key from evidence dict
            def get_evidence_field(field):
                val = evidence.get(field.lower())
                if val is None:
                    val = evidence.get(field.upper())
                print(f"[skill-debug] Field '{field}' lookup: {'Found' if val else 'Missing'}")
                if val:
                    print(f"[skill-debug] Field '{field}' keys: {list(val.keys()) if isinstance(val, dict) else 'Not a dict'}")
                return val

            print(f"[skill-debug] Payload Keys: {list(payload.keys())}")
            if 'evidence' in payload:
                print(f"[skill-debug] Evidence Keys: {list(payload['evidence'].keys())}")

            # Use appropriate field mapping from builder.build_evidence_graph
            graph = builder.build_evidence_graph(
                ats_output=get_evidence_field('ats'),
                github_output=get_evidence_field('github'),
                linkedin_output=get_evidence_field('linkedin'),
                leetcode_output=get_evidence_field('leetcode'),
                codeforces_output=get_evidence_field('codeforces'),
                evaluation_id=str(payload.get('application_id', ''))
            )
            print(f"[skill-debug] Graph Skills: {list(graph.get('skills', {}).keys())}")
            
            # Step 2: Run Verification Agent
            agent_impl = SkillVerificationAgentV2()
            result = agent_impl.issue_credential(evidence_graph=graph)
        except Exception as e:
            import traceback
            print(f"[skill] Error in handler: {str(e)}")
            traceback.print_exc()
            result = {"error": str(e), "agent": "skill"}

        # Sync callers wait on this
        agent.set_response(message.message_id, dump_json(result))

    agent.add_message_handler(handler)

def main():
    agent = build_agent()
    attach_handler(agent)

    print(f"[skill] Agent ID: {agent.agent_id}")
    print(f"[skill] Webhook URL: {agent.webhook_url}")
    print(f"[skill] Registry URL: {agent.agent_config.registry_url}")
    print(f"[skill] Capabilities: {agent.agent_config.capabilities}")

    import signal, sys, time
    def _shutdown(sig, frame):
        print("\n[skill] Shutting down gracefully...")
        sys.exit(0)
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
