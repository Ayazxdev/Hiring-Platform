"""
Normalizes data from different sources into unified format
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    Converts raw scraper outputs into standardized schema
    """
    
    def normalize_github(self, raw_github: Dict) -> Dict:
        """
        Normalize GitHub scraper output
        
        Args:
            raw_github: Raw JSON from GitHub scraper (flat or nested format)
            
        Returns:
            Normalized GitHub metrics
        """
        try:
            # Support both nested (data.key) and flat (key) formats
            data = raw_github.get("data", raw_github)
            
            # Extract project scores
            project_scores = [
                p.get("project_score", 0) 
                for p in data.get("projects", [])
            ]
            avg_project_quality = (
                sum(project_scores) / len(project_scores) 
                if project_scores else 0
            )
            
            # Calculate commits score (normalize to 0-100)
            # Assumption: 200+ commits/year = 100, 0 commits = 0
            total_commits = data.get("total_commits_last_year", 0)
            commits_score = min(int((total_commits / 200) * 100), 100)
            
            # Consistency score can be 0-10 scale, normalize to 0-100
            raw_consistency = data.get("consistency_score", 0)
            consistency_score = min(raw_consistency * 10, 100) if raw_consistency <= 10 else raw_consistency
            
            return {
                "commits_score": commits_score,
                "consistency_score": consistency_score,
                "project_quality": int(avg_project_quality),
                "skills_detected": data.get("top_languages", []),
                "raw_data": data
            }
            
        except Exception as e:
            logger.error(f"GitHub normalization failed: {e}")
            return {
                "commits_score": 0,
                "consistency_score": 0,
                "project_quality": 0,
                "skills_detected": [],
                "raw_data": {}
            }
    
    def normalize_leetcode(self, raw_leetcode: Dict) -> Dict:
        """
        Normalize LeetCode scraper output
        
        Args:
            raw_leetcode: Raw JSON from LeetCode scraper (flat or nested format)
            
        Returns:
            Normalized LeetCode metrics
        """
        try:
            # Support both nested (data.key) and flat (key) formats
            data = raw_leetcode.get("data", raw_leetcode)
            
            # Calculate problem-solving score
            # Easy: 1 point, Medium: 3 points, Hard: 5 points
            difficulty = data.get("difficulty_breakdown", {})
            weighted_score = (
                difficulty.get("easy", 0) * 1 +
                difficulty.get("medium", 0) * 3 +
                difficulty.get("hard", 0) * 5
            )
            
            # Normalize to 0-100 (500 points = 100)
            problem_solving_score = min(int((weighted_score / 500) * 100), 100)
            
            # Parse contest rating
            contest_rating_str = data.get("contest_rating", "Unrated")
            max_rating = data.get("max_rating")
            if contest_rating_str == "Unrated" or not max_rating:
                competitive_rating = 0
            else:
                # Normalize rating (2500+ = 100, 1000 = 40)
                competitive_rating = min(int((max_rating / 2500) * 100), 100)
            
            return {
                "problem_solving_score": problem_solving_score,
                "competitive_rating": competitive_rating,
                "skills_detected": [data.get("top_language", "")] if data.get("top_language") else [],
                "raw_data": data
            }
            
        except Exception as e:
            logger.error(f"LeetCode normalization failed: {e}")
            return {
                "problem_solving_score": 0,
                "competitive_rating": 0,
                "skills_detected": [],
                "raw_data": {}
            }
    
    def normalize_codechef(self, raw_codechef: Dict) -> Dict:
        """
        Normalize CodeChef scraper output
        
        Args:
            raw_codechef: Raw JSON from CodeChef scraper (flat or nested format)
            
        Returns:
            Normalized CodeChef metrics
        """
        try:
            # Support both nested (data.key) and flat (key) formats
            data = raw_codechef.get("data", raw_codechef)
            
            # Normalize rating (2500+ = 100)
            rating = data.get("rating", 0)
            competitive_rating = min(int((rating / 2500) * 100), 100)
            
            # Normalize problems solved (500+ = 100)
            problems = data.get("problems_solved", 0)
            problem_solving_score = min(int((problems / 500) * 100), 100)
            
            return {
                "problem_solving_score": problem_solving_score,
                "competitive_rating": competitive_rating,
                "skills_detected": [data.get("top_language", "")] if data.get("top_language") else [],
                "raw_data": data
            }
            
        except Exception as e:
            logger.error(f"CodeChef normalization failed: {e}")
            return {
                "problem_solving_score": 0,
                "competitive_rating": 0,
                "skills_detected": [],
                "raw_data": {}
            }
    
    def normalize_all(
        self, 
        github_json: Optional[Dict] = None,
        leetcode_json: Optional[Dict] = None,
        codechef_json: Optional[Dict] = None
    ) -> Dict:
        """
        Normalize all available data sources
        
        Args:
            github_json: Raw GitHub data (optional)
            leetcode_json: Raw LeetCode data (optional)
            codechef_json: Raw CodeChef data (optional)
            
        Returns:
            Unified normalized data
        """
        normalized = {}
        
        if github_json:
            normalized["github"] = self.normalize_github(github_json)
        
        if leetcode_json:
            normalized["leetcode"] = self.normalize_leetcode(leetcode_json)
        
        if codechef_json:
            normalized["codechef"] = self.normalize_codechef(codechef_json)
        
        return normalized
