import os
import json
import time
import threading
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from zyndai_agent.agent import AgentConfig, ZyndAIAgent
from zyndai_agent.message import AgentMessage

load_dotenv()

class ZyndOrchestrator:
    """Thin client to call other Zynd agents via /webhook/sync.

    Why this exists:
      - Existing backend expects request/response (synchronous) calls.
      - Zynd supports synchronous webhooks via /webhook/sync where the receiver sets a response
        using set_response(message_id, ...).
    """

    def __init__(self):
        # Calculate REPO_ROOT relative to this file (backend/app/zynd_orchestrator.py)
        import pathlib
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        
        cfg = AgentConfig(
            name="FairHiring Orchestrator",
            description="Orchestrates FairHiring network and routes tasks to specialized Zynd agents.",
            capabilities={
                "ai": ["orchestration"],
                "protocols": ["http"],
                "services": ["fair_hiring", "orchestrator"]
            },
            webhook_host=os.getenv("ZYND_WEBHOOK_HOST", "0.0.0.0"),
            webhook_port=int(os.getenv("ORCH_ZYND_PORT", "5100")),
            registry_url=os.getenv("ZYND_REGISTRY_URL", "https://registry.zynd.ai"),
            api_key=os.getenv("ZYND_API_KEY"),
            identity_credential_path=os.path.abspath(os.path.join(repo_root, os.getenv("ORCH_ZYND_VC", "credentials/orchestrator_vc.json"))),
            config_dir=os.getenv("ORCH_ZYND_CONFIG_DIR", ".agent-orchestrator"),
        )
        self.agent = ZyndAIAgent(agent_config=cfg)

    def _sync_url(self, webhook_url: str) -> str:
        # Most agents register httpWebhookUrl ending with /webhook
        if webhook_url.endswith("/webhook"):
            return webhook_url + "/sync"
        if webhook_url.endswith("/webhook/"):
            return webhook_url + "sync"
        # Fallback
        return webhook_url.rstrip("/") + "/webhook/sync"

    def discover(self, capabilities: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        # 1. Local Fallback Logic (Prioritized for local development)
        # Mapping capabilities to local ports from .env
        port_map = {
            "matching": os.getenv("MATCHING_ZYND_PORT", "5101"),
            "bias_detection": os.getenv("BIAS_ZYND_PORT", "5102"),
            "skill_verification": os.getenv("SKILL_ZYND_PORT", "5103"),
            "ats": os.getenv("ATS_ZYND_PORT", "5104"),
            "passport": os.getenv("PASSPORT_ZYND_PORT", "5105"),
            "github": os.getenv("GITHUB_ZYND_PORT", "5106"),
            "github_analysis": os.getenv("GITHUB_ZYND_PORT", "5106"),
            "linkedin": os.getenv("LINKEDIN_ZYND_PORT", "5107"),
            "leetcode_analysis": os.getenv("LEETCODE_ZYND_PORT", "5108"),
            "codeforces_analysis": os.getenv("CODEFORCES_ZYND_PORT", "5109"),
        }
        
        local_results = []
        for cap in capabilities:
            if cap in port_map:
                port = port_map[cap]
                webhook_host = os.getenv("ZYND_WEBHOOK_HOST", "localhost")
                local_results.append({
                    "name": f"Local {cap} Agent",
                    "didIdentifier": f"did:zynd:0x{cap.upper()}_LOCAL",
                    "httpWebhookUrl": f"http://{webhook_host}:{port}/webhook"
                })
        
        # 2. Registry Discovery
        try:
            results = self.agent.search_agents_by_capabilities(capabilities=capabilities, top_k=top_k)
            if results:
                # Merge: Local first, then registry ones
                return local_results + results
        except Exception as e:
            print(f"[zynd-orch] Discovery error: {e}")
        
        return local_results

    def call_sync(self, target_agent: Dict[str, Any], payload: Dict[str, Any], message_type: str = "query", timeout: int = 500) -> Dict[str, Any]:
        target_name = target_agent.get("name", "Unknown")
        target_did = target_agent.get("didIdentifier", "Unknown")
        print(f"[zynd-orch] Protocol: ZYND-HTTP-SYNC | Target: {target_name} ({target_did})")
        
        self.agent.connect_agent(target_agent)
        sync_url = self._sync_url(self.agent.target_webhook_url)

        msg = AgentMessage(
            content=json.dumps(payload, ensure_ascii=False),
            sender_id=self.agent.agent_id,
            message_type=message_type,
            sender_did=self.agent.identity_credential
        )

        # NOTE: use raw requests to /webhook/sync to get immediate response
        resp = requests.post(sync_url, json=msg.to_dict(), timeout=timeout, headers={"Content-Type":"application/json"})
        data = resp.json()
        if data.get("status") != "success":
            return {"error": data.get("error", "zynd_sync_failed"), "raw": data}

        # Receiver returns 'response' as string; we try to parse JSON
        response_str = data.get("response")
        if isinstance(response_str, (dict, list)):
            return response_str
        try:
            return json.loads(response_str)
        except Exception:
            return {"response": response_str, "raw": data}

# Singleton
_orchestrator: Optional[ZyndOrchestrator] = None

def get_orchestrator() -> ZyndOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ZyndOrchestrator()
    return _orchestrator
