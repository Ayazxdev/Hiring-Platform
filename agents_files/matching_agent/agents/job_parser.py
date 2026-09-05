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
    Uses protected OpenRouter calls with safe fallbacks.
    """
    
    def __init__(self):
        self.client = None
        api_key = (
            os.getenv("OPENROUTER_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("API_KEY") or
            OPENROUTER_API_KEY
        )
        base_url = os.getenv("OPENAI_API_BASE") or OPENROUTER_BASE_URL
        
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
            logger.warning("[MATCHING] OpenAI client not initialized. Using fallback.")
            return self._fallback_extraction(job_description)

        try:
            logger.info("[MATCHING] Calling OpenRouter for JD extraction (Model: openai/gpt-4o-mini)...")
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini", # ✅ SAFE WORKING MODEL
                messages=[
                    {"role": "system", "content": "Extract required technical skills from the job description. Return a JSON list of strings."},
                    {"role": "user", "content": job_description}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Expecting {"required_skills": [...]} or similar
            if isinstance(data, dict):
                skills = data.get("required_skills", data.get("skills", []))
            else:
                skills = data if isinstance(data, list) else []
                
            if not skills:
                raise ValueError("No skills extracted by LLM")
                
            return {"strict_requirements": skills}

        except Exception as e:
            logger.error(f"[MATCHING] LLM extraction failed: {e}")
            print(f"[MATCHING] 🔄 Using fallback skill extraction due to error: {e}")
            return self._fallback_extraction(job_description)

    def _fallback_extraction(self, job_description: str) -> Dict[str, Any]:
        """
        Safe fallback: Simple keyword extractor to prevent pipeline breaks.
        """
        print("[MATCHING] Using fallback skill extraction")
        # Very simple heuristic: words with length > 3 that look like tech
        # In a real system, this would use a local keyword list
        common_tech = ["python", "javascript", "react", "node", "aws", "docker", "sql", "java", "fastapi"]
        
        words = job_description.lower().split()
        potential_skills = []
        
        for word in words:
            word = word.strip(".,:;()[]")
            if word in common_tech and word not in potential_skills:
                potential_skills.append(word.capitalize())
            elif len(word) > 4 and word[0].isupper() and word not in potential_skills:
                # Add capitalized words that might be names/tech
                potential_skills.append(word)

        # Ensure we have something
        if not potential_skills:
            potential_skills = [w.strip(".,") for w in words if len(w) > 5][:10]

        return {"strict_requirements": potential_skills[:15]}
