import os
import json
import requests
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class DualLLMClient:
    """
    Hybrid LLM Client:
    - Ollama (Local/Free): Default for extraction.
    - OpenRouter (Cloud/Paid): For security/deep checks.
    """
    
    def __init__(self, openrouter_api_key: Optional[str] = None):
        # Flexible key lookup
        self.openrouter_api_key = (
            openrouter_api_key or 
            os.getenv("OPENROUTER_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or
            os.getenv("API_KEY")
        )
        
        # Ollama Config (kept as backup only)
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2") 
        
        # OpenRouter / Gemini Config
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not self.openrouter_api_key and gemini_key and not gemini_key.startswith("your_"):
            self.openrouter_api_key = gemini_key
            self.openrouter_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            self.cloud_model = os.getenv("LLM_MODEL") or "gemini-1.5-flash"
        else:
            self.openrouter_url = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
            if not self.openrouter_url.endswith("/chat/completions"):
                self.openrouter_url = self.openrouter_url.rstrip("/") + "/chat/completions"
            self.cloud_model = os.getenv("LLM_MODEL") or os.getenv("OPENROUTER_MODEL") or "anthropic/claude-3-haiku"

    def call_ollama(self, prompt: str, system_prompt: str = "") -> Dict:
        """Execute prompt on Local Ollama."""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            payload = {
                "model": self.ollama_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_ctx": 4096}
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=(3.0, 30.0))
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                return {"content": content, "success": True, "model": "ollama"}
            else:
                logger.error(f"Ollama Error {response.status_code}: {response.text}")
                return {"content": "", "success": False, "error": f"Status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Ollama Connection Failed: {e}")
            return {"content": "", "success": False, "error": str(e)}

    def call_openrouter(self, prompt: str, system_prompt: str = "") -> Dict:
        """Execute prompt on OpenRouter."""
        if not self.openrouter_api_key:
            return {"content": "", "success": False, "error": "No API Key"}
            
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.cloud_model,
                "messages": messages,
                "temperature": 0.1
            }
            
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://antigravity.agent",
                "X-Title": "ATS Security"
            }
            
            response = requests.post(self.openrouter_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return {"content": content, "success": True, "model": "openrouter"}
            else:
                logger.error(f"OpenRouter Error {response.status_code}: {response.text}")
                return {"content": "", "success": False, "error": f"Status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"OpenRouter Failed: {e}")
            return {"content": "", "success": False, "error": str(e)}

    def extract_json(self, text: str) -> Dict:
        """Helper to parse JSON from Markdown."""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}
