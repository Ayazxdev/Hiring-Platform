"""
Skill Verification Agent V2 (2026 Architecture)

THE DECISION-MAKING LAYER

This is NOT a parser. This is the hiring brain that:
- Processes Evidence Graph
- Calculates portfolio scores
- Determines signal strength
- Triggers conditional tests
- Issues final credentials

Core Principle: Skills verified ONLY via GitHub/coding platforms.
ATS/LinkedIn can NEVER add skills, only boost confidence.
"""
import json
import logging
import hashlib
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Ontology Imports
try:
    from ..utils.ontology_loader import SKILL_DB
    from ..skill_classifier import classify_skill
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.ontology_loader import SKILL_DB
    from skill_classifier import classify_skill

logger = logging.getLogger(__name__)

# Trust Weights (2026 Evidence-Based Architecture)
TRUST_WEIGHTS = {
    "github": 0.45,
    "ats_resume": 0.25,
    "linkedin": 0.15,
    "leetcode": 0.10,
    "codeforces": 0.10
}

# Thresholds
WEAK_SIGNAL_THRESHOLD = 0.6  # If verified/claimed < 0.6, trigger test
# Note: HIGH_CONFIDENCE_THRESHOLD removed as it was unused


def normalize_weights(weights: Dict, available_sources: List[str]) -> Dict:
    """
    Normalize weights to handle missing signals.
    
    If a signal is missing (e.g., no Codeforces), redistribute its weight
    proportionally among available sources.
    
    Args:
        weights: Original trust weights
        available_sources: List of available source names
    
    Returns:
        Normalized weights that sum to 1.0
    """
    active = {k: v for k, v in weights.items() if k in available_sources}
    total = sum(active.values())
    
    if total == 0:
        return {}
    
    return {k: v / total for k, v in active.items()}





class SemanticIntegrityChecker:
    """
    2026 Defense: Cross-source narrative validation
    Checks if resume claims match GitHub/LinkedIn evidence
    """
    
    def verify_experience_claims(
        self,
        resume_text: str = "", # Optional if we use stats
        ats_data: dict = None,
        github_data: dict = None,
        linkedin_data: dict = None
    ) -> dict:
        """
        Validate that resume claims are supported by evidence
        """
        # If we don't have GitHub data, we can't verify code history
        if not github_data:
            return {"discrepancy_detected": False, "reason": "No GitHub data"}
            
        # 1. Experience Years Validation
        # Get years from ATS extracted data instead of raw text parsing if possible
        claimed_years = 0
        if ats_data and "experience" in ats_data:
             # Heuristic: count distinct years in experience
             # Real implementation would be more robust
             claimed_years = len(ats_data.get("experience", [])) * 1.5 # Avg 1.5 yr per role? generic fallback
        
        # Or try to extract from raw text if passed (as user code suggested)
        if resume_text:
             extracted = self._extract_years_claimed(resume_text)
             if extracted > claimed_years:
                 claimed_years = extracted
        
        # GitHub account age
        github_years = github_data.get("credibility_signal", {}).get("account_age_years", 0)
        
        # Valid: Claim can be > GitHub age (worked before GitHub), 
        # but if claim is > 5 years and GitHub is < 1, it's suspicious for a "Senior" dev
        if claimed_years > 5 and github_years < 1:
            return {
                "discrepancy_detected": True,
                "type": "experience_inflation",
                "claimed_years": claimed_years,
                "verified_years": github_years,
                "severity": "medium",
                "action": "flag_for_interview"
            }
        
        # 2. Leadership Validation
        if self._detect_leadership_claims(resume_text or str(ats_data)):
             # User logic: check for team work
             if not self._check_github_team_work(github_data):
                  return {
                    "discrepancy_detected": True,
                    "type": "leadership_unverified",
                    "severity": "low", # Lower severity as GitHub isn't always for work
                    "action": "flag_for_interview_verification"
                }

        return {"discrepancy_detected": False}
    
    def _extract_years_claimed(self, text: str) -> int:
        import re
        patterns = [r'(\d+)\+?\s*years?', r'(\d+)-\d+\s*years?']
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            years.extend([int(m) for m in matches])
        return max(years) if years else 0

    def _detect_leadership_claims(self, text: str) -> bool:
        keywords = ["led team", "managed team", "director", "manager", "head of", "lead", "vp"]
        return any(kw in text.lower() for kw in keywords)

    def _check_github_team_work(self, github_data: dict) -> bool:
        # Check if they have organization memberships or PR reviews (schema dependent)
        # Using simple heuristic from available signals
        # If credibility score is high, assume some collaboration
        score = github_data.get("credibility_signal", {}).get("score", 0)
        return score > 40


class SkillVerificationAgentV2:
    """
    The final decision-making agent.
    
    Input: Evidence Graph (from evidence_graph_builder.py)
    Output: Skill Credential with test triggers and signal strength
    """
    
    def __init__(self, db_session=None):
        self.credential = {}
        self.db_session = db_session
        
        # Initialize Human Review Service (Centralized)
        if self.db_session or True: # Always try to init
            try:
                from services.human_review_service import HumanReviewService
                self.human_review_service = HumanReviewService()
            except ImportError:
                try:
                    import sys
                    from pathlib import Path
                    sys.path.append(str(Path(__file__).parent.parent.parent))
                    from services.human_review_service import HumanReviewService
                    self.human_review_service = HumanReviewService()
                except ImportError:
                    logger.warning("Could not import HumanReviewService. Human-in-loop disabled.")
                    self.human_review_service = None
    
    def issue_credential(self, evidence_graph: Dict) -> Dict:
        """
        Main entry point: Issue skill credential from evidence graph.
        """
        logger.info("Issuing skill credential...")
        
        # 0. Identity from Envelope/Context
        evaluation_id = evidence_graph.get("evaluation_id")
        if not evaluation_id:
             logger.warning("No evaluation_id provided. Using fallback.")
             evaluation_id = "unknown_eval_id"

        # 1. Extract Signals
        signals = evidence_graph.get("signals", {})
        github_data = signals.get("github", evidence_graph.get("github", {}))
        ats_data = signals.get("ats_resume", evidence_graph.get("ats_resume", {}))
        linkedin_data = signals.get("linkedin", evidence_graph.get("linkedin", {}))
        leetcode_data = signals.get("leetcode", evidence_graph.get("leetcode", {}))
        codeforces_data = signals.get("codeforces", evidence_graph.get("codeforces", {}))
        
        # 2. Skills are used as-is from Evidence Graph
        # REMOVED: Mutation of skill graph here. Verification should be read-only for stability.
        # Skills should be injected by EvidenceGraphBuilder.
        if "evidence_graph" in evidence_graph:
            skills = evidence_graph["evidence_graph"].get("skills", {})
        else:
            skills = evidence_graph.get("skills", {})
        
        # 3. Cleanup & Standardization + Ontology Verification
        cleaned_skills = {}
        NOISE_TOOLS = ["vs code", "github", "git", "gitlab", "bitbucket", "npm", "yarn"]
        
        # Prepare combined evidence text for verification
        # 2026 Fix: Combine all available text signals for more robust pattern matching
        evidence_text = ""
        if ats_data and "raw_text" in ats_data:
            evidence_text += ats_data["raw_text"] + "\n"
        
        # Add GitHub project descriptions and READMEs if available
        if github_data and "data" in github_data:
            repo_data = github_data["data"]
            if isinstance(repo_data, dict) and "projects" in repo_data:
                for proj in repo_data["projects"]:
                    evidence_text += proj.get("name", "") + " " + proj.get("description", "") + "\n"

        for skill, data in skills.items():
            s_lower = skill.lower()
            if s_lower in NOISE_TOOLS: continue
            
            # Use display name or language if nested
            fixed_name = skill
            if isinstance(data, dict) and "language" in data:
                fixed_name = data["language"]
            
            if "t ailwind" in s_lower: fixed_name = "Tailwind CSS"
            
            # --- NEW: Ontology Verification ---
            v_res = self.verify_skill(fixed_name, evidence_text)
            if v_res and v_res.get("verified"):
                # Augment skill data with verification evidence
                if not isinstance(data, dict): data = {"status": "self_attested"}
                data["verified_by_ontology"] = True
                data["ontology_confidence"] = v_res.get("confidence", 0.5)
                data["ontology_evidence"] = v_res.get("evidence", [])
                
                # Boost confidence if pattern matched
                current_conf = data.get("confidence", 0.5)
                data["confidence"] = min(1.0, current_conf + (v_res.get("confidence", 0.5) * 0.2))
            
            cleaned_skills[fixed_name] = data
        
        skills = cleaned_skills # Update local ref

        # 4. Check Manipulation
        # (Assuming _check_manipulation method exists below)
        manipulation = self._check_manipulation(ats_data)
        if manipulation["severity"] == "critical":
             # Should implement blacklist logic here properly, but for now:
             logger.warning("Critical manipulation detected.")

        # 4.5 Semantic Integrity Check (2026 Defense)
        integrity_checker = SemanticIntegrityChecker()
        # ATS data usually contains raw text in 'raw_text' or similar if preserved, 
        # otherwise we assume we have access or fallback to metadata
        integrity_result = integrity_checker.verify_experience_claims(
            resume_text=ats_data.get("raw_text", "") if ats_data else "",
            ats_data=ats_data,
            github_data=github_data,
            linkedin_data=linkedin_data
        )
        
        if integrity_result["discrepancy_detected"]:
            logger.warning(f"Integrity Discrepancy: {integrity_result['type']}")
            if "flags" not in manipulation: manipulation["flags"] = []
            manipulation["flags"].append(f"Integrity: {integrity_result['type']}")
            if manipulation["severity"] == "low":
                manipulation["severity"] = integrity_result["severity"]

        # 4.6 SUBMIT FOR HUMAN REVIEW (Centralized Logic)
        if manipulation["severity"] in ["critical", "high"] and self.human_review_service:
            # Prepare review event
            candidate_id = ats_data.get("email") or evaluation_id
            triggered_by = "skill_verification"
            
            # Aggregate Evidence
            evidence_payload = {
                "manipulation": manipulation,
                "integrity_check": integrity_result,
                "ats_semantic_flags": ats_data.get("semantic_flags", []),
                "github_stats": {k: v for k, v in github_data.get("credibility_signal", {}).items() if k in ["score", "account_age_years"]}
            }
            
            # Submit
            reason = f"Manipulation detected: {manipulation['severity'].upper()} severity. Flags: {', '.join(manipulation.get('flags', []))}"
            
            review_id = self.human_review_service.submit_review_request(
                candidate_id=candidate_id,
                triggered_by=triggered_by,
                severity=manipulation["severity"],
                reason=reason,
                system_action_taken="blocked" if manipulation["severity"] == "critical" else "flagged",
                evidence=evidence_payload,
                job_id="unknown_job"
            )
            logger.info(f"Submitted Human Review Request: {review_id}")

        # 5. Portfolio Score
        portfolio_score = self._calculate_portfolio_score(
            github_data, leetcode_data, codeforces_data, ats_data, linkedin_data
        )
        
        # 6. Skill Confidence & Signal Strength
        # Granular manipulation penalties based on severity
        if manipulation["severity"] == "low":
            manipulation_penalty = 1.0  # No penalty
        elif manipulation["severity"] == "medium":
            manipulation_penalty = 0.85  # 15% penalty
        elif manipulation["severity"] == "high":
            manipulation_penalty = 0.60  # 40% penalty
        elif manipulation["severity"] == "critical":
            manipulation_penalty = 0.30  # 70% penalty
        else:
            manipulation_penalty = 1.0  # Default to no penalty
        
        skill_confidence = round(portfolio_score * manipulation_penalty)
        
        if skill_confidence >= 70:
            signal_strength = "strong"
            test_required = False
        elif 40 <= skill_confidence < 70:
            signal_strength = "weak"
            test_required = True
        else:
            signal_strength = "none"
            test_required = True

        # 7. Confidence Explanation
        if skill_confidence > 80:
            conf_explanation = "High confidence backed by strong code evidence and consistent history."
        elif skill_confidence > 50:
            conf_explanation = "Moderate confidence. Portfolio presence confirmed but deep code evidence is partial."
        else:
            conf_explanation = "Low confidence. Relying primarily on self-attested claims without code backing."
        
        if test_required:
            conf_explanation += " Targeted testing recommended."

        # 8. Tier Skills
        verified_skills_tiered = self._tier_skills(skills)
        
        # 9. Credential Status
        credential_status = "VERIFIED"
        if test_required: credential_status = "PENDING_TEST"
        if manipulation["severity"] == "critical": credential_status = "Revoked (Manipulation)"

        # 10. Construct Output
        credential_output = {
            "credential_id": f"cred_{uuid.uuid4().hex[:8]}",
            "evaluation_id": evaluation_id,
            "verified_skills": verified_skills_tiered,
            "skill_confidence": skill_confidence,
            "confidence_explanation": conf_explanation,
            "signal_strength": signal_strength,
            "credential_status": credential_status,
            "test_required": test_required,
            "next_stage": "conditional_test" if test_required else "bias_detection",
            "evidence_summary": {
                 "signal_count": len(signals),
                 "conflict_flags": evidence_graph.get("confidence_controls", {}).get("conflict_flags", [])
            }
        }

        # Return Shared Envelope
        return {
            "evaluation_id": evaluation_id,
            "agent": "skill_verification",
            "version": "2026.1",
            "output": credential_output
        }
    
    def verify_skill(self, skill: str, evidence_text: str) -> Optional[Dict[str, Any]]:
        """
        Verify a skill using ontology patterns against evidence text.
        
        Args:
            skill: The skill name to verify
            evidence_text: The text to search for patterns (GitHub code, ATS text, etc.)
            
        Returns:
            Verification result dict if skill is in ontology, else None
        """
        skill_data = SKILL_DB.get(skill)
        if not skill_data:
            return None

        matches = []
        # Check verification methods (patterns) defined in ontology
        for lang, patterns in skill_data.get("verification_methods", {}).items():
            for p in patterns:
                if p.lower() in evidence_text.lower():
                    matches.append(p)

        # Also check interface patterns if present
        for lang, patterns in skill_data.get("interface_patterns", {}).items():
            for p in patterns:
                if p.lower() in evidence_text.lower():
                    matches.append(p)

        if matches:
            return {
                "skill": skill,
                "type": "framework",
                "verified": True,
                "confidence": skill_data.get("confidence_weight", 0.5),
                "evidence": list(set(matches)) # Unique matches
            }

        return {
            "skill": skill,
            "type": "framework",
            "verified": False,
            "confidence": 0.0
        }
    
    def _tier_skills(self, skills: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize skills into tiers for better matching precision.
        Returns objects with name and score.
        """
        tiers = {
            "core": [],
            "frameworks": [],
            "infrastructure": [],
            "tools": []
        }
        
        # Dynamic taxonomy from ontology + fallback
        # ANYTHING in ontology is considered a framework/system
        
        for skill_name, data in skills.items():
            skill_lower = skill_name.lower()
            categorized = False
            
            # 1. Use Ontology Classifier (Gold Standard)
            s_type = classify_skill(skill_name)
            
            # Extract score (0.0 to 1.0 -> 0 to 100)
            conf = data.get("confidence", 0.0)
            score = int(conf * 100) if conf <= 1.0 else int(conf)
            
            skill_obj = {"name": skill_name, "score": score}
            
            if s_type == "framework":
                tiers["frameworks"].append(skill_obj)
                categorized = True
            elif s_type == "language":
                tiers["core"].append(skill_obj)
                categorized = True
            
            # 2. Legacy Taxonomy Fallback (if not in ontology)
            if not categorized:
                TAXONOMY = {
                    "core": ["algorithms", "data structures", "machine learning", "deep learning", "computer vision", "nlp"],
                    "infrastructure": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "linux", "unix", "bash", "shell"],
                    "tools": ["git", "github", "gitlab", "postman", "vs code", "jira", "trello", "slack", "office", "excel", "powerpoint"]
                }
                
                for tier, keywords in TAXONOMY.items():
                    if any(k == skill_lower for k in keywords):
                        tiers[tier].append(skill_obj)
                        categorized = True
                        break
            
            # 3. Final Fallback based on common heuristics
            if not categorized:
                if "framework" in skill_lower or ".js" in skill_lower or "library" in skill_lower:
                    tiers["frameworks"].append(skill_obj)
                elif "tool" in skill_lower:
                    tiers["tools"].append(skill_obj)
                elif "cloud" in skill_lower or "infra" in skill_lower:
                    tiers["infrastructure"].append(skill_obj)
                else:
                    # Default high-value to core
                    tiers["core"].append(skill_obj)
                    
        return tiers

    def _generate_candidate_id(self, evidence_graph: Dict) -> str:
        """
        [DEPRECATED] Generate anonymized candidate ID.
        Kept only for fallback if evaluation_id is missing in dev.
        """
        github = evidence_graph.get("signals", {}).get("github", {})
        
        # Try GitHub username first
        if github and github.get("data"):
            username = github["data"].get("username")
            if username:
                hash_obj = hashlib.sha256(username.encode())
                return f"anon_{hash_obj.hexdigest()[:8]}"
        
        # Fallback to generic ID
        return evidence_graph.get("candidate_id", "anon_unknown")
    
    def _calculate_portfolio_score(
        self, 
        github_data: Dict,
        leetcode_data: Dict = None,
        codeforces_data: Dict = None,
        ats_data: Dict = None,
        linkedin_data: Dict = None
    ) -> int:
        """
        Calculate portfolio score using weighted signals.
        
        Formula:
        portfolio_score = Sum(score[i] * weight[i])
        """
        signal_scores = {}
        github_status = github_data.get("github_status", "complete") if github_data else "unavailable"
        
        # GitHub score (from credibility + best repos)
        # FIX: Relaxed success flag requirement - allow partial GitHub data to contribute
        if github_data:
            # Check for explicit success flag OR presence of meaningful data
            has_success_flag = github_data.get("success", False)
            has_meaningful_data = (
                github_data.get("activity_score") is not None or
                github_data.get("credibility_signal", {}).get("score") is not None or
                len(github_data.get("repos", [])) > 0
            )
            
            if has_success_flag or has_meaningful_data:
                # FIX: Support both flattened (Service) and nested (Raw) schemas
                credibility = github_data.get("activity_score") 
                if credibility is None: # Fallback
                    credibility = github_data.get("credibility_signal", {}).get("score", 0)
                
                # Repos might be at top level (Service) or nested (Raw)
                best_repos = github_data.get("repos", []) # Service Schema
                if not best_repos:
                    best_repos = github_data.get("skill_signal", {}).get("best_repositories", []) # Raw Schema
                
                if best_repos:
                    avg_repo_score = sum(r.get("best_repo_score", 0) for r in best_repos) / len(best_repos)
                else:
                    # If partial, don't punish with zero
                    avg_repo_score = 45 if github_status == "partial" else 0
                
                # GitHub signal = 60% credibility + 40% project quality
                github_score = int((credibility * 0.6) + (avg_repo_score * 0.4))
                
                # CLAMP: If partial data, ensure we don't drop below a neutral floor
                if github_status == "partial":
                    github_score = max(github_score, 35)
                    
                signal_scores["github"] = github_score
                logger.debug(f"GitHub score: {github_score} (cred={credibility}, repos={avg_repo_score:.1f}, status={github_status})")
        
        # LeetCode score
        if leetcode_data:
            problems_solved = leetcode_data.get("problems_solved", 0)
            contest_rating = leetcode_data.get("contest_rating", 0)
            
            problems_score = min(100, (problems_solved / 300) * 100) if problems_solved else 0
            rating_score = min(100, (contest_rating / 3000) * 100) if contest_rating else 0
            
            leetcode_score = int((problems_score * 0.7) + (rating_score * 0.3))
            signal_scores["leetcode"] = leetcode_score
        
        # Codeforces score
        if codeforces_data:
            rating = codeforces_data.get("rating", 0)
            codeforces_score = min(100, int((rating / 2400) * 100)) if rating else 0
            signal_scores["codeforces"] = codeforces_score
        
        # ATS score
        if ats_data:
            target_data = ats_data.get("evidence", ats_data)
            semantic_flags = target_data.get("semantic_flags", [])
            skills_count = len(target_data.get("skills", []))
            experience_count = len(target_data.get("experience", []))
            
            base_score = min(60, (skills_count * 3) + (experience_count * 10))
            ats_score = max(0, base_score - (len(semantic_flags) * 10))
            signal_scores["ats_resume"] = ats_score
        
        # LinkedIn score
        if linkedin_data:
            exp_data = linkedin_data.get("experience", {})
            skills_data = linkedin_data.get("skills", {})
            
            has_experience = bool((exp_data.get("timeline") or exp_data.get("positions") or exp_data.get("total_years")) if isinstance(exp_data, dict) else exp_data)
            has_skills = bool(skills_data.get("claimed", []) if isinstance(skills_data, dict) else skills_data)
            
            linkedin_score = 65 if (has_experience and has_skills) else (35 if has_experience or has_skills else 10)
            signal_scores["linkedin"] = linkedin_score
        
        # Normalize weights only for sources that actually exist and gave a non-None score
        available_sources = list(signal_scores.keys())
        normalized_weights = normalize_weights(TRUST_WEIGHTS, available_sources)
        
        # Calculate weighted portfolio score
        portfolio_score = 0
        for source, score in signal_scores.items():
            weight = normalized_weights.get(source, 0)
            portfolio_score += score * weight
            logger.debug(f"  {source}: {score} * {weight:.2f} = {score * weight:.1f}")
        
        final_score = round(portfolio_score)
        
        # Hard safety net against false zeros
        if final_score == 0 and len(signal_scores) > 0:
            final_score = 10 # Minimal heartbeat score if ANY evidence exists
            
        logger.info(f"Portfolio score calculated: {final_score} from {len(signal_scores)} sources ({github_status})")
        
        return final_score

    
    def _determine_signal_strength(
        self, 
        skill_confidence: int,
        manipulation_severity: str,
        test_required: bool
    ) -> str:
        """Determine overall signal strength"""
        if manipulation_severity != "low":
            return "weak"
            
        if skill_confidence >= 80:
            return "very_strong"
        elif skill_confidence >= 70:
            return "strong"
        elif skill_confidence >= 50:
            return "moderate"
        else:
            return "weak"
    
    def _check_manipulation(self, ats_data: Dict) -> Dict:
        """Check for manipulation signals"""
        if not ats_data:
            return {
                "detected": False,
                "severity": "low",
                "action": "proceed",
                "flags": []
            }
        
        # Check if manipulation was detected by ATS agent
        # (ATS agent already has manipulation detection built-in)
        manipulation_detected = False
        severity = "low"
        flags = []
        
        # Check for semantic flags (from ATS)
        # Skip flags with no real issue description (placeholder/empty flags)
        PLACEHOLDER_ISSUES = {"no issue specified", "none", "", None}
        semantic_flags = [
            f for f in ats_data.get("semantic_flags", [])
            if str(f.get("issue", "") or "").lower().strip() not in PLACEHOLDER_ISSUES
        ]
        if semantic_flags:
            manipulation_detected = True
            # Determine severity based on flag types
            high_severity_types = ["impossible_timeline"]  # timeline_overlap alone is not high severity
            if any(flag.get("severity") == "high" and flag.get("type") in high_severity_types for flag in semantic_flags):
                severity = "high"
            elif any(flag.get("type") in ["timeline_overlap", "impossible_timeline"] for flag in semantic_flags):
                severity = "medium"

            flags = [f"{flag.get('type')}: {flag.get('issue')}" for flag in semantic_flags]
        
        # Determine action
        if severity == "critical":
            action = "blacklist"
        elif severity == "high":
            action = "flag_for_review"
        else:
            action = "proceed"
        
        return {
            "detected": manipulation_detected,
            "severity": severity,
            "action": action,
            "flags": flags
        }
    
    def _build_evidence_details(
        self, 
        github_data: Dict, 
        leetcode_data: Dict
    ) -> Dict:
        """Build evidence details section"""
        details = {}
        
        # GitHub details
        if github_data:
            profile = github_data.get("profile", {})
            
            # FIX: Support Service Schema (Flattened) vs Raw Schema (Nested)
            if "activity_score" in github_data:
                # Service Schema
                cred_score = github_data.get("activity_score", 0)
                top_langs = github_data.get("frameworks", [])
                # Commits can be in "commits" dict or we estimate
                commits_data = github_data.get("commits", {})
                commits_analyzed = commits_data.get("total_commits_analyzed", 0)
                project_quality = 0 # Not directly exposed in flat schema easily unless stored
            else:
                # Raw Schema
                credibility = github_data.get("credibility_signal", {})
                skill_signal = github_data.get("skill_signal", {})
                cred_score = credibility.get("score", 0)
                top_langs = skill_signal.get("verified_languages", [])
                
                best_repos = skill_signal.get("best_repositories", [])
                project_quality = int(sum(r.get("best_repo_score", 0) for r in best_repos) / len(best_repos)) if best_repos else 0
                commits_analyzed = sum(
                    r.get("details", {}).get("commit_analysis", {}).get("author_commits", 0) 
                    for r in best_repos
                )

            details["github"] = {
                "username": self._redact_pii(profile.get("username", github_data.get("username", ""))), 
                "credibility_score": cred_score,
                "commits_analyzed": commits_analyzed,
                "project_quality": project_quality,
                "top_languages": top_langs[:5], # Show top 5
                "account_age_years": github_data.get("credibility_signal", {}).get("account_age_years", 0) 
            }
        
        # LeetCode details (if available)
        if leetcode_data:
            details["leetcode"] = {
                "problems_solved": leetcode_data.get("problems_solved", 0),
                "contest_rating": leetcode_data.get("contest_rating", 0),
                "level": leetcode_data.get("level", "N/A"),
                "top_language": leetcode_data.get("top_language", "N/A")
            }
        
        return details

    def _redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        if not text:
            return ""
        return "REDACTED"

    def _anonymize_repos(self, repos: List[Dict]) -> List[Dict]:
        """Anonymize repository details for public credential"""
        anonymized = []
        for repo in repos:
            # Create a clean copy with only skill evidence data
            clean_repo = {
                "repo_name": repo.get("repo_name"), # Repo name is usually generic enough
                "language": repo.get("language"),
                "description": "REDACTED", # Description might contain PII
                "best_repo_score": repo.get("best_repo_score"),
                "category": repo.get("category"),
                "why_selected": repo.get("why_selected", []),
                "signals": repo.get("signals", {})
            }
            anonymized.append(clean_repo)
        return anonymized
    
    def _get_available_sources(self, evidence_graph: Dict) -> List[str]:
        """Get list of available evidence sources"""
        sources = []
        signals = evidence_graph.get("signals", {})
        
        if signals.get("github"):
            sources.append("github")
        if signals.get("ats_resume"):
            sources.append("ats_resume")
        if signals.get("linkedin"):
            sources.append("linkedin")
        if signals.get("leetcode"):
            sources.append("leetcode")
        # Map codechef key to codeforces (temporary fix until we rename everywhere)
        if signals.get("codechef") or signals.get("codeforces"):
            sources.append("codeforces")
        
        return sources
    
    def _determine_credential_status(
        self, 
        signal_strength: str, 
        manipulation_severity: str,
        test_required: bool
    ) -> str:
        """Determine final credential status"""
        if manipulation_severity == "critical":
            return "BLACKLISTED"
        elif manipulation_severity == "high":
            return "FLAGGED_FOR_REVIEW"
        elif test_required:
            return "PROVISIONAL"  # Needs test to confirm
        elif signal_strength == "strong":
            return "VERIFIED"
        else:
            return "CONDITIONAL"  # Moderate signal, may need interview
    
    def _build_blacklist_credential(
        self, 
        evidence_graph: Dict, 
        manipulation: Dict
    ) -> Dict:
        """Build credential for blacklisted candidate"""
        candidate_id = self._generate_candidate_id(evidence_graph)
        
        return {
            "candidate_id": candidate_id,
            "credential_status": "BLACKLISTED",
            "manipulation_analysis": manipulation,
            "reason": "Critical manipulation detected in application materials",
            "next_stage": "END_PIPELINE",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_metadata": {
                "agent": "skill_verification_agent_v2",
                "version": "2026.1",
                "decision_layer": True
            }
        }


# CLI for testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python skill_verification_agent_v2.py <evidence_graph.json>")
        print("Example: python skill_verification_agent_v2.py evidence_graph_output.json")
        sys.exit(1)
    
    # Load evidence graph
    evidence_graph_path = sys.argv[1]
    
    try:
        with open(evidence_graph_path, 'r', encoding='utf-8-sig') as f:
            evidence_graph = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load evidence graph: {e}")
        sys.exit(1)
    
    # Issue credential
    agent = SkillVerificationAgentV2()
    credential = agent.issue_credential(evidence_graph)
    
    # Display result
    print("\n" + "="*60)
    print("🎓 SKILL CREDENTIAL ISSUED")
    print("="*60)
    print(json.dumps(credential, indent=2, default=str))
    
    # Summary
    print("\n" + "="*60)
    print("📊 DECISION SUMMARY")
    print("="*60)
    print(f"Status: {credential.get('credential_status')}")
    print(f"Verified Skills: {len(credential.get('verified_skills', []))}")
    print(f"Signal Strength: {credential.get('signal_strength')}")
    print(f"Test Required: {credential.get('test_required')}")
    print(f"Next Stage: {credential.get('next_stage')}")
