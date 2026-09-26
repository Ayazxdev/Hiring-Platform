import json
import logging
import os
from typing import List, Dict, Any
from openai import OpenAI
from ..config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

logger = logging.getLogger(__name__)

class JobParserAgent:
    """
    Agent to extract structured requirements from raw job descriptions.
    Uses Gemini or OpenRouter with safe fallbacks.
    """
    
    def __init__(self):
        self.client = None
        api_key = None
        base_url = None
        self.model_name = "gemini-3.8-flash"

        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and not gemini_key.startswith("your_"):
            api_key = gemini_key
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            self.model_name = "gemini-3.8-flash"
        else:
            raw_or_key = os.getenv("OPENROUTER_API_KEY") or OPENROUTER_API_KEY
            if raw_or_key and not raw_or_key.startswith("your_"):
                api_key = raw_or_key
                base_url = os.getenv("OPENAI_API_BASE") or OPENROUTER_BASE_URL
                self.model_name = os.getenv("LLM_MODEL") or "openai/gpt-4o-mini"
            elif os.getenv("OPENAI_API_KEY") and not os.getenv("OPENAI_API_KEY").startswith("your_"):
                api_key = os.getenv("OPENAI_API_KEY")
                base_url = os.getenv("OPENAI_API_BASE") or "https://api.openai.com/v1"
                self.model_name = os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
        if api_key:
            try:
                self.client = OpenAI(
                    base_url=base_url,
                    api_key=api_key,
                )
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def extract_requirements(self, job_description: str) -> Dict[str, Any]:
        """
        Extract required skills from job description using LLM with fallback.
        """
        if not self.client:
            logger.warning("[MATCHING] LLM client not initialized. Using fallback.")
            return self._fallback_extraction(job_description)

        try:
            logger.info(f"[MATCHING] Calling LLM for JD extraction (Model: {self.model_name})...")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a job parser. Extract required technical skills from the job description. Return JSON with 'required_skills' (array of strings, e.g. ['Python', 'Docker'])."
                    },
                    {
                        "role": "user",
                        "content": f"Extract required skills from this JD:\n\n{job_description}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            if isinstance(data, dict):
                skills = data.get("required_skills", data.get("skills", []))
            else:
                skills = data if isinstance(data, list) else []
                
            if not skills:
                raise ValueError("No skills extracted by LLM")
                
            return {"strict_requirements": skills}

        except Exception as e:
            logger.warning(f"[MATCHING] LLM extraction failed: {e}. Using fallback.")
            return self._fallback_extraction(job_description)

    def _fallback_extraction(self, job_description: str) -> Dict[str, Any]:
        """
        Safe fallback: Keyword extractor covering common languages, systems, and tools.
        """
        logger.info("[MATCHING] Using fallback skill extraction")
        import re
        known_tech = [
            "Python", "C++", "Rust", "Java", "JavaScript", "TypeScript", "Go",
            "Docker", "Docker Compose", "CI/CD", "Git", "REST APIs", "gRPC", "FastAPI",
            "Node.js", "React", "Next.js", "PostgreSQL", "MongoDB", "Databases", "DBMS",
            "Operating Systems", "Object-Oriented Programming", "Data Structures & Algorithms",
            "System Design", "Distributed Systems", "Asynchronous Programming", "Concurrent Programming",
            "PyTorch", "ONNX", "NLP", "Vector Search", "LLMs", "MCP"
        ]
        
        extracted = []
        for tech in known_tech:
            escaped = re.escape(tech)
            if tech == "C++":
                if re.search(r'(?:\bC\+\+(?!\w)|\bCPP\b)', job_description, re.I):
                    extracted.append(tech)
            elif re.search(rf'\b{escaped}\b', job_description, re.I):
                extracted.append(tech)

        if not extracted:
            extracted = ["Python", "Backend", "APIs", "Git", "Docker"]

        return {"strict_requirements": extracted}
