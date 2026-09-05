"""
LLM Parser with Dual Backend Support

Supports:
- Ollama (local) - for development/offline use
- OpenRouter (cloud) - for production/API use

Toggle via config.py LLM_BACKEND setting.
"""
import os
import sys
import json
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import get_prompt_for_platform, GITHUB_CONSISTENCY_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfileParser:
    """
    Unified parser that can use either Ollama or OpenRouter LLMs.
    """
    
    def __init__(self, backend: str = "openrouter", model: str = None):
        """
        Initialize parser with specified backend.
        """
        self.backend = backend.lower()
        
        if self.backend == "ollama":
            self._init_ollama(model or os.getenv("OLLAMA_MODEL", "llama3.2"))
        elif self.backend == "openrouter":
            self._init_openrouter(model or os.getenv("LLM_MODEL") or "anthropic/claude-3-haiku")
        else:
            raise ValueError(f"Unknown backend: {backend}. Use 'ollama' or 'openrouter'.")
        
        logger.info(f"ProfileParser initialized with backend: {self.backend}")
    
    def _init_ollama(self, model: str):
        """Initialize Ollama client"""
        try:
            from langchain_ollama import OllamaLLM
            self.llm = OllamaLLM(model=model)
            self.model_name = model
        except ImportError:
            logger.error("langchain_ollama not installed. Run: pip install langchain-ollama")
            raise
    
    def _init_openrouter(self, model: str):
        """Initialize OpenRouter client"""
        try:
            from langchain_openai import ChatOpenAI
            
            # Robust API key lookup
            api_key = (
                os.getenv("OPENROUTER_API_KEY") or 
                os.getenv("OPENAI_API_KEY") or 
                os.getenv("API_KEY")
            )
            
            if not api_key:
                try:
                    from config import OPENROUTER_API_KEY
                    api_key = OPENROUTER_API_KEY
                except ImportError:
                    pass
            
            if not api_key:
                logger.warning("OPENROUTER_API_KEY not found. Attempting to proceed but LLM calls may fail.")
            
            base_url = os.getenv("OPENAI_API_BASE") or "https://openrouter.ai/api/v1"
            
            self.llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key or "missing_key",
                model=model,
                temperature=0.1
            )
            self.model_name = model
        except ImportError:
            logger.error("langchain_openai not installed. Run: pip install langchain-openai")
            raise
    
    def parse_platform(self, raw_text: str, platform: str) -> Dict:
        """
        Parse raw scraped text for a specific platform.
        
        Args:
            raw_text: Raw text content from scraper
            platform: Platform name (LeetCode, CodeChef, etc.)
            
        Returns:
            Parsed JSON data
        """
        logger.info(f"Parsing {platform} profile with {self.backend}...")
        
        # Get prompt template
        prompt_template = get_prompt_for_platform(platform)
        prompt = prompt_template.format(raw_text=raw_text[:20000])  # Limit context
        
        try:
            # Call LLM
            response = self.llm.invoke(prompt)
            
            # Handle both Ollama (string) and OpenRouter (object)
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Parse JSON response
            parsed = self._parse_json(content)
            logger.info(f"Successfully parsed {platform} profile")
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse {platform}: {e}")
            return {"error": str(e)}
    
    def parse_github_consistency(self, github_stats: Dict) -> Dict:
        """
        Analyze GitHub consistency with LLM.
        
        Args:
            github_stats: Stats from get_contribution_history()
            
        Returns:
            Consistency analysis with score and persona
        """
        logger.info("Analyzing GitHub consistency...")
        
        prompt = GITHUB_CONSISTENCY_PROMPT.format(
            period=github_stats.get("period", "Unknown"),
            total_commits=github_stats.get("total_commits", 0),
            max_gap=github_stats.get("max_gap", 0),
            commits_last_30_days=github_stats.get("commits_last_30_days", 0),
            days_since_last_commit=github_stats.get("days_since_last_commit", 0),
            monthly_log=github_stats.get("monthly_log", {})
        )
        
        try:
            response = self.llm.invoke(prompt)
            
            # Handle both Ollama (string) and OpenRouter (object)
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            parsed = self._parse_json(content)
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to analyze GitHub: {e}")
            return {
                "consistency_score": 5,
                "persona": "Unknown",
                "reasoning": f"Analysis failed: {e}"
            }
    
    def _parse_json(self, llm_response: str) -> Dict:
        """
        Safely parse JSON from LLM response.
        
        Args:
            llm_response: Raw LLM output
            
        Returns:
            Parsed dictionary
        """
        try:
            # Clean response
            cleaned = llm_response.strip()
            
            # Remove markdown code fences
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            # Find JSON object
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = cleaned[start:end]
                return json.loads(json_str)
            
            return {"error": "No JSON found in response", "raw": cleaned[:500]}
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {"error": str(e), "raw": llm_response[:500]}


# Legacy function for backward compatibility
def parse_with_ollama(dom_chunks: List[str], parse_description: str) -> str:
    """
    Legacy function to maintain compatibility with existing code.
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        
    Returns:
        Parsed result as string
    """
    parser = ProfileParser(backend="openrouter")
    
    results = []
    for i, chunk in enumerate(dom_chunks, start=1):
        # Determine platform from description
        platform = "Generic"
        if "leetcode" in parse_description.lower():
            platform = "LeetCode"
        elif "codechef" in parse_description.lower():
            platform = "CodeChef"
        elif "codeforces" in parse_description.lower():
            platform = "Codeforces"
        elif "github" in parse_description.lower():
            platform = "GitHub"
        elif "linkedin" in parse_description.lower():
            platform = "LinkedIn"
        
        result = parser.parse_platform(chunk, platform)
        results.append(json.dumps(result, indent=2))
        logger.info(f"Parsed batch: {i} of {len(dom_chunks)}")
    
    return "\n".join(results)
