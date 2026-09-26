# pyright: reportMissingImports=false

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..utils.match_normalizer import MatchNormalizer # type: ignore
from .job_parser import JobParserAgent

logger = logging.getLogger(__name__)

class MatchingAgent:
    """
    Stage 5: Transparent Matching Agent (v2 Gold Standard - Hardened)
    
    Architecture: Pure function matching. No file-path logic inside the core.
    Formula: Deterministic 4-pillar scoring [Core 40%, Frameworks 25%, Evidence 20%, Growth 15%]
    """
    
    def __init__(self):
        self.job_parser = JobParserAgent()

    def match_candidate(self, candidate_credential: Dict, job_requirements: Any, experience_years: int = 0, protocall_result: Optional[Dict] = None) -> Dict:
        """
        Compatibility method for LangGraph nodes.
        Wraps the main matching logic.
        """
        # If job_requirements is a string (raw JD), parse it first
        if isinstance(job_requirements, str):
            logger.info("[MATCHING] job_requirements is a string. Parsing with JobParserAgent...")
            job_requirements = self.job_parser.extract_requirements(job_requirements)
            
        # Ensure candidate has the necessary fields
        candidate = candidate_credential.copy()
        candidate["experience_years"] = experience_years
        if protocall_result:
            candidate["protocall_result"] = protocall_result
            
        return self.match(job_requirements, candidate)

    def match(self, jd: Dict, candidate: Dict) -> Dict:
        """
        Main entry point for matching.
        Expects JD v3 and SkillAgent v3 (normalized) as dictionaries.
        """
        # 1. Validation & Normalization
        try:
            jd_norm = MatchNormalizer.normalize_job(jd)
            cand_norm = MatchNormalizer.normalize_candidate(candidate)
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return {"error": "Invalid Input Schema", "details": str(e)}

        # 2. Calculate Pillars (Refined Scoring Logic + Experience)
        core_score = self._score_core(jd_norm, cand_norm)           # 35%
        framework_score = self._score_frameworks(jd_norm, cand_norm) # 20%
        experience_score = self._score_experience(jd_norm, cand_norm) # 20%
        evidence_score = self._score_evidence(jd_norm, cand_norm)   # 15%
        learning_score = self._score_learning(jd_norm, cand_norm)   # 10%

        # 3. Aggregate Final Score
        final_score = round(core_score + framework_score + experience_score + evidence_score + learning_score, 3) # type: ignore
        
        # 4. Determine Decision Band (Machine-Safe Enums)
        decision_enum, status_enum = self._band_decision(final_score)

        return {
            "match_score": round(final_score * 100), # Legacy support (0-100)
            "match_status": status_enum,
            "decision_reason": decision_enum,
            "final_score": final_score,
            "breakdown": {
                "core_skills": round(core_score, 3), # type: ignore
                "frameworks_tools": round(framework_score, 3), # type: ignore
                "experience": round(experience_score, 3), # type: ignore
                "evidence": round(evidence_score, 3), # type: ignore
                "learning_velocity": round(learning_score, 3) # type: ignore
            },
            "analysis": {
                "matched_skills": list(set(cand_norm.get("verified_skills", [])) & set(jd_norm.get("strict_requirements", []))),
                "missing_skills": list(set(jd_norm.get("strict_requirements", [])) - set(cand_norm.get("verified_skills", [])))
            },
            "timestamp": datetime.now().isoformat()
        }

    def _score_core(self, jd: Dict, cand: Dict) -> float:
        """Pillar 1: Core Skills (35% Weight)"""
        core_set = set(jd.get("strict_requirements", []) + jd.get("languages", []) + jd.get("web_fundamentals", []))

        if not core_set:
            return 0.35  # Defensive default

        verified = set(cand.get("verified_skills", []))
        matches = verified & core_set
        return (len(matches) / len(core_set)) * 0.35

    def _score_frameworks(self, jd: Dict, cand: Dict) -> float:
        """Pillar 2: Frameworks & Tools (20% Weight)"""
        frameworks = set(jd.get("frontend_frameworks", []) + jd.get("backend_frameworks", []))
        infra = set(jd.get("infrastructure_concepts", []) + jd.get("backend_concepts", []))
        tools = set(jd.get("developer_tools", []))
        soft = set(jd.get("soft_requirements", []))
        verified = set(cand.get("verified_skills", []))

        fw_match = len(verified & frameworks) / len(frameworks) if frameworks else 1.0
        infra_match = len(verified & infra) / len(infra) if infra else 1.0
        tool_match = len(verified & tools) / len(tools) if tools else 1.0
        soft_match = len(verified & soft) / len(soft) if soft else 1.0

        pillar_score = (0.40 * fw_match + 0.25 * tool_match + 0.20 * infra_match + 0.15 * soft_match)
        return pillar_score * 0.20
        
    def _score_experience(self, jd: Dict, cand: Dict) -> float:
        """Pillar 3: Experience (20% Weight) - Rewards relevant work history"""
        experience_list = cand.get("experience", [])
        years = float(cand.get("experience_years", 0) or 0)
        if not experience_list and years <= 0:
            return 0.0
            
        # Give up to 20% based on amount and quality of claims or responsibilities or years
        total_claims = sum(len(exp.get("claims", []) or exp.get("responsibilities", [])) for exp in experience_list)
        # Factor in years of experience (e.g. 1-2 years for junior dev is full score)
        years_score = min(years / 2.0, 1.0) if years > 0 else 0.0
        claims_score = min(total_claims / 3.0, 1.0) if total_claims > 0 else 0.0
        
        combined_ratio = max(years_score, claims_score, (years_score + claims_score) / 2.0)
        return round(min(0.20, combined_ratio * 0.20), 3)

    def _score_evidence(self, jd: Dict, cand: Dict) -> float:
        """Pillar 4: Evidence Signals (15% Weight)"""
        github_raw = cand.get("github_score", 0.0)
        github_score = min(max(github_raw, 0.0), 1.0)
        github_contrib = github_score * 0.10
        
        cp_activity = cand.get("cp_activity", False)
        if cp_activity or github_score > 0.6:
            cp_contrib = 0.05
        else:
            cp_contrib = 0.0

        # Hackathon bonus — JD explicitly rewards this signal
        hackathon_contrib = 0.05 if cand.get("has_hackathon", False) else 0.0
            
        return min(0.15, github_contrib + cp_contrib + hackathon_contrib)

    def _score_learning(self, jd: Dict, cand: Dict) -> float:
        """Pillar 5: Learning Velocity (10% Weight)"""
        velocity_raw = cand.get("learning_velocity", 0.5)
        velocity = min(max(velocity_raw, 0.0), 1.0)
        weight = jd.get("matching_philosophy", {}).get("learning_velocity_weight", 0.2)
        return velocity * weight * 0.10

    def _band_decision(self, score: float):
        if score >= 0.75: return "STRONG_MATCH", "MATCHED"
        if score >= 0.55: return "GOOD_MATCH", "CONDITIONAL_MATCH"
        if score >= 0.40: return "POTENTIAL_MATCH", "POTENTIAL"
        return "NO_MATCH", "REJECTED"

    # COMPATIBILITY LAYER (DEPRECATED)
    def _calculate_match(self, credential: Dict, job: Dict) -> Dict:
        return self.match(job, credential)

    def _load_json(self, path: str) -> Dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
