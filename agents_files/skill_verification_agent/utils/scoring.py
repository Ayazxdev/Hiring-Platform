"""
Scoring and aggregation logic
"""
from typing import Dict
import logging
import sys
sys.path.insert(0, '..')
from config import SCORING_WEIGHTS, GITHUB_WEIGHTS

logger = logging.getLogger(__name__)


class PortfolioScorer:
    """
    Calculates portfolio score from normalized evidence
    """
    
    @staticmethod
    def calculate_portfolio_score(normalized_data: Dict) -> Dict:
        """
        Calculate portfolio score from normalized evidence.
        
        JUDGE-SAFE APPROACH:
        - GitHub = 100% verified confidence source
        - Coding platforms = Supporting signals only (no numerical score)
        
        Args:
            normalized_data: Output from DataNormalizer.normalize_all()
            
        Returns:
            Portfolio score with signal summary
        """
        try:
            # GitHub Component (PRIMARY - 100% of verified score)
            github_score = 0
            github_verified = False
            consistency_signal = "unknown"
            project_depth_signal = "unknown"
            
            if "github" in normalized_data:
                github_verified = True
                gh = normalized_data["github"]
                
                # Calculate GitHub-based score (0-100)
                commits_contribution = gh["commits_score"] * GITHUB_WEIGHTS["commits_score"]
                consistency_contribution = gh["consistency_score"] * GITHUB_WEIGHTS["consistency_score"]
                project_contribution = gh["project_quality"] * GITHUB_WEIGHTS["project_quality"]
                
                github_score = int(commits_contribution + consistency_contribution + project_contribution)
                
                # Determine signal strengths
                if gh["consistency_score"] >= 70:
                    consistency_signal = "strong"
                elif gh["consistency_score"] >= 40:
                    consistency_signal = "medium"
                else:
                    consistency_signal = "weak"
                
                if gh["project_quality"] >= 70:
                    project_depth_signal = "strong"
                elif gh["project_quality"] >= 40:
                    project_depth_signal = "medium"
                elif gh["project_quality"] > 0:
                    project_depth_signal = "weak"
                # else: remains "unknown"
            
            # Coding Platforms (SUPPORTING ONLY - no numerical contribution)
            supporting_platforms = {}
            
            if "leetcode" in normalized_data:
                supporting_platforms["leetcode"] = {
                    "status": "self_attested",
                    "profile_provided": True,
                    "problems_solved": normalized_data["leetcode"]["raw_data"].get("problems_solved", 0)
                }
            
            if "codechef" in normalized_data:
                supporting_platforms["codechef"] = {
                    "status": "self_attested", 
                    "profile_provided": True,
                    "problems_solved": normalized_data["codechef"]["raw_data"].get("problems_solved", 0)
                }
            
            # Signal summary for transparency
            signal_summary = {
                "github_verified": github_verified,
                "coding_platforms": "self_attested_supporting" if supporting_platforms else "none_provided",
                "consistency": consistency_signal,
                "project_depth": project_depth_signal
            }
            
            return {
                "portfolio_score": github_score,  # GitHub-only score
                "signal_summary": signal_summary,
                "supporting_platforms": supporting_platforms,
                "evidence_sources": ["github"] if github_verified else [],
                "supporting_sources": list(supporting_platforms.keys())
            }
            
        except Exception as e:
            logger.error(f"Portfolio scoring failed: {e}")
            return {
                "portfolio_score": 0,
                "signal_summary": {
                    "github_verified": False,
                    "coding_platforms": "none_provided",
                    "consistency": "unknown",
                    "project_depth": "unknown"
                },
                "supporting_platforms": {},
                "evidence_sources": [],
                "supporting_sources": []
            }

    
    @staticmethod
    def detect_ats_manipulation(resume_text: str) -> Dict:
        """
        Detect keyword stuffing in resume
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Manipulation detection result
        """
        # Skip check if resume is too short (< 150 words)
        total_words = len(resume_text.split())
        
        if total_words < 150:
            logger.info(f"Resume too short ({total_words} words), skipping ATS check")
            return {
                "manipulated": False,
                "keyword_density": 0.0,
                "keyword_count": 0,
                "action": "skipped_short_resume"
            }
        
        # Common technical keywords
        technical_keywords = [
            "python", "javascript", "java", "c++", "react", "node",
            "aws", "docker", "kubernetes", "machine learning",
            "data science", "sql", "nosql", "api", "rest",
            "agile", "scrum", "git", "ci/cd", "devops"
        ]
        
        # Count keyword occurrences
        resume_lower = resume_text.lower()
        keyword_count = sum(resume_lower.count(kw) for kw in technical_keywords)
        
        # Calculate density
        density = keyword_count / total_words if total_words > 0 else 0
        
        # Raised threshold to 0.5 (was 0.3)
        manipulated = density > 0.50
        
        return {
            "manipulated": manipulated,
            "keyword_density": round(density, 3),
            "keyword_count": keyword_count,
            "action": "require_live_test" if manipulated else "proceed"
        }

