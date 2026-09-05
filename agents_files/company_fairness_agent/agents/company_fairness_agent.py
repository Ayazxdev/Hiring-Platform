"""
Company Fairness Verification Agent

Verifies job descriptions for bias BEFORE candidates enter the pipeline.
Only companies with score >= 60 are allowed to proceed.
"""
import os
import sys
import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    COMPANY_FAIRNESS_MODEL,
    MODEL_TEMPERATURE,
    MINIMUM_FAIRNESS_SCORE,
    SEVERE_PENALTY,
    MODERATE_PENALTY,
    MINOR_PENALTY,
    GENDERED_KEYWORDS,
    AGE_BIAS_KEYWORDS,
    COLLEGE_BIAS_KEYWORDS,
    EXPERIENCE_INFLATION_PATTERNS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompanyFairnessAgent:
    """
    Agent 1: Company Fairness Verification
    
    Input: Job description
    Output: Fairness score (0-100)
    
    Checks:
    - Gendered language ("rockstar", "ninja")
    - Age bias ("young team")
    - College requirements
    - Experience inflation
    
    Critical Rule: Only score >= 60 enters pipeline
    """
    
    def __init__(self):
        """Initialize agent with LLM"""
        api_key = (
            os.getenv("OPENROUTER_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("API_KEY") or
            OPENROUTER_API_KEY
        )
        base_url = os.getenv("OPENAI_API_BASE") or OPENROUTER_BASE_URL
        
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key or "missing_key",
            model=COMPANY_FAIRNESS_MODEL,
            temperature=MODEL_TEMPERATURE
        )
        
        if not api_key:
            logger.warning("No API key found for CompanyFairnessAgent. LLM calls will likely fail.")
        
        logger.info(f"CompanyFairnessAgent initialized with model: {COMPANY_FAIRNESS_MODEL}")
    
    def verify_company(self, job_description: str, company_id: Optional[str] = None) -> Dict:
        """
        Main verification method
        
        Args:
            job_description: Full job description text
            company_id: Optional company identifier
            
        Returns:
            Fairness verification result
        """
        logger.info("=" * 60)
        logger.info("STARTING COMPANY FAIRNESS VERIFICATION")
        logger.info("=" * 60)
        
        # Generate company ID if not provided
        if not company_id:
            company_id = self._generate_company_id(job_description)
        
        # Step 1: Keyword-based scanning (fast, cheap)
        keyword_flags = self._scan_keywords(job_description)
        
        # Step 2: LLM-based analysis (nuanced, more expensive)
        llm_analysis = self._analyze_with_llm(job_description)
        
        # Step 3: Calculate final score
        final_result = self._calculate_fairness_score(keyword_flags, llm_analysis)
        
        # Step 4: Generate suggestions
        suggestions = self._generate_suggestions(keyword_flags, llm_analysis)
        
        # Determine status
        status = "Approved" if final_result["fairness_score"] >= MINIMUM_FAIRNESS_SCORE else "Rejected"
        
        result = {
            "company_id": company_id,
            "fairness_score": final_result["fairness_score"],
            "status": status,
            "flags": final_result["flags"],
            "suggestions": suggestions,
            "breakdown": final_result["breakdown"],
            "verified_at": datetime.now().isoformat(),
            "can_proceed": status == "Approved"
        }
        
        logger.info(f"Fairness Score: {result['fairness_score']}, Status: {status}")
        logger.info("=" * 60)
        
        return result
    
    def _generate_company_id(self, jd: str) -> str:
        """Generate unique company ID from JD hash"""
        hash_obj = hashlib.sha256(jd[:200].encode())
        return f"company_{hash_obj.hexdigest()[:8]}"
    
    def _scan_keywords(self, jd: str) -> Dict:
        """
        Fast keyword-based bias detection
        
        Args:
            jd: Job description text
            
        Returns:
            Detected bias flags
        """
        logger.info("Scanning for biased keywords...")
        
        jd_lower = jd.lower()
        flags = []
        
        # Check gendered keywords
        for keyword in GENDERED_KEYWORDS:
            if keyword.lower() in jd_lower:
                flags.append({
                    "type": "gender",
                    "keyword": keyword,
                    "severity": "moderate",
                    "penalty": MODERATE_PENALTY
                })
        
        # Check age bias
        for keyword in AGE_BIAS_KEYWORDS:
            if keyword.lower() in jd_lower:
                flags.append({
                    "type": "age",
                    "keyword": keyword,
                    "severity": "severe",
                    "penalty": SEVERE_PENALTY
                })
        
        # Check college bias
        for keyword in COLLEGE_BIAS_KEYWORDS:
            if keyword.lower() in jd_lower:
                flags.append({
                    "type": "college",
                    "keyword": keyword,
                    "severity": "severe",
                    "penalty": SEVERE_PENALTY
                })
        
        # Check experience inflation
        for pattern in EXPERIENCE_INFLATION_PATTERNS:
            matches = re.findall(pattern, jd_lower)
            for match in matches:
                flags.append({
                    "type": "experience_inflation",
                    "keyword": match,
                    "severity": "moderate",
                    "penalty": MODERATE_PENALTY
                })
        
        logger.info(f"Found {len(flags)} keyword-based flags")
        
        return {
            "flags": flags,
            "total_penalty": sum(f["penalty"] for f in flags)
        }
    
    def _analyze_with_llm(self, jd: str) -> Dict:
        """
        LLM-based nuanced bias analysis
        
        Args:
            jd: Job description text
            
        Returns:
            LLM analysis result
        """
        logger.info("Running LLM bias analysis...")
        
        prompt = f"""You are a hiring bias detection expert. Analyze this job description for hidden biases.

JOB DESCRIPTION:
{jd}

DETECT THESE BIASES:
1. **Gender Bias**: Masculine-coded words (aggressive, dominant), feminine-coded words that might exclude
2. **Age Bias**: Terms suggesting preference for young/old candidates
3. **Educational Bias**: Unnecessary degree requirements, prestige bias
4. **Experience Inflation**: Unrealistic experience requirements for the role level
5. **Cultural Bias**: Location-specific requirements that aren't job-essential

RULES:
- Only flag ACTUAL bias, not neutral terms
- Consider context (e.g., "aggressive sales targets" is different from "aggressive personality")
- Rate each bias as: none, minor, moderate, severe

Return JSON ONLY (no markdown):
{{
  "biases_detected": [
    {{
      "type": "gender|age|education|experience|cultural",
      "evidence": "quoted text from JD",
      "severity": "minor|moderate|severe",
      "explanation": "why this is biased"
    }}
  ],
  "overall_bias_level": "low|medium|high",
  "positive_aspects": ["list of inclusive language used"],
  "llm_penalty": 0-30
}}
"""
        
        try:
            response = self.llm.invoke(prompt)
            result = self._parse_llm_json(response.content)
            
            logger.info(f"LLM detected {len(result.get('biases_detected', []))} biases")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {
                "biases_detected": [],
                "overall_bias_level": "unknown",
                "positive_aspects": [],
                "llm_penalty": 0
            }
    
    def _parse_llm_json(self, llm_response: str) -> Dict:
        """Safely parse LLM JSON response"""
        try:
            cleaned = llm_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            return {
                "biases_detected": [],
                "overall_bias_level": "unknown",
                "positive_aspects": [],
                "llm_penalty": 0
            }
    
    def _calculate_fairness_score(self, keyword_flags: Dict, llm_analysis: Dict) -> Dict:
        """
        Calculate final fairness score
        
        Args:
            keyword_flags: Results from keyword scanning
            llm_analysis: Results from LLM analysis
            
        Returns:
            Final score with breakdown
        """
        # Start with 100
        base_score = 100
        
        # Deduct keyword penalties
        keyword_penalty = keyword_flags["total_penalty"]
        
        # Deduct LLM penalties
        llm_penalty = llm_analysis.get("llm_penalty", 0)
        
        # Calculate final score (minimum 0)
        final_score = max(0, base_score - keyword_penalty - llm_penalty)
        
        # Combine all flags
        all_flags = keyword_flags["flags"].copy()
        for bias in llm_analysis.get("biases_detected", []):
            all_flags.append({
                "type": bias.get("type", "unknown"),
                "keyword": bias.get("evidence", ""),
                "severity": bias.get("severity", "minor"),
                "explanation": bias.get("explanation", "")
            })
        
        return {
            "fairness_score": final_score,
            "flags": all_flags,
            "breakdown": {
                "base_score": base_score,
                "keyword_penalty": keyword_penalty,
                "llm_penalty": llm_penalty,
                "final_score": final_score
            }
        }
    
    def _generate_suggestions(self, keyword_flags: Dict, llm_analysis: Dict) -> List[str]:
        """
        Generate actionable suggestions to improve JD
        
        Args:
            keyword_flags: Results from keyword scanning
            llm_analysis: Results from LLM analysis
            
        Returns:
            List of suggestions
        """
        suggestions = []
        
        # Suggestions for keyword flags
        keyword_replacements = {
            "rockstar": "skilled professional",
            "ninja": "expert",
            "guru": "specialist",
            "wizard": "experienced developer",
            "hacker": "engineer",
            "aggressive": "driven",
            "young team": "dynamic team",
            "digital native": "tech-savvy"
        }
        
        for flag in keyword_flags["flags"]:
            keyword = flag["keyword"].lower()
            if keyword in keyword_replacements:
                suggestions.append(
                    f"Replace '{flag['keyword']}' with '{keyword_replacements[keyword]}'"
                )
            else:
                suggestions.append(f"Remove or rephrase '{flag['keyword']}'")
        
        # Add LLM-based suggestions
        for bias in llm_analysis.get("biases_detected", []):
            if bias.get("explanation"):
                suggestions.append(bias["explanation"])
        
        # Add positive reinforcement
        if llm_analysis.get("positive_aspects"):
            suggestions.append(
                f"Keep these inclusive elements: {', '.join(llm_analysis['positive_aspects'][:3])}"
            )
        
        return suggestions[:10]  # Limit to 10 suggestions
