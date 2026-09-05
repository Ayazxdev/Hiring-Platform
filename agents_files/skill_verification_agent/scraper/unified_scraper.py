"""
Unified Scraper - Main Entry Point

Scrapes all platforms and returns a single unified JSON per candidate.
This is the main module that integrates scraping + parsing + schema validation.
"""
import os
import sys
import json
import hashlib
import logging
from typing import Dict, Optional, List
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add parent directory for config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrape import (
    identify_platform,
    scrape_website,
    scrape_dynamic_page,
    get_contribution_history,
    get_contribution_count,
    get_project_details
)
from parse import ProfileParser
from schemas import (
    UnifiedCandidateProfile,
    GitHubProfile,
    LeetCodeProfile,
    CodeChefProfile,
    CodeforcesProfile,
    DifficultyBreakdown
)

# GitHub API imports
try:
    from github_api import GitHubAPIClient
    from config import GITHUB_PAT, GITHUB_USE_API
    GITHUB_API_AVAILABLE = True
except ImportError:
    GITHUB_API_AVAILABLE = False
    GITHUB_PAT = None
    GITHUB_USE_API = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedScraper:
    """
    Unified scraper that:
    1. Takes URLs for multiple platforms
    2. Scrapes each platform
    3. Parses with LLM
    4. Returns a single unified JSON
    """
    
    def __init__(self, llm_backend: str = "ollama", llm_model: str = None):
        """
        Initialize scraper.
        
        Args:
            llm_backend: "ollama" or "openrouter"
            llm_model: Model name (optional)
        """
        self.parser = ProfileParser(backend=llm_backend, model=llm_model)
        logger.info(f"UnifiedScraper initialized with LLM backend: {llm_backend}")
    
    def scrape_candidate(
        self,
        candidate_email: str,
        github_url: Optional[str] = None,
        leetcode_url: Optional[str] = None,
        codechef_url: Optional[str] = None,
        codeforces_url: Optional[str] = None,
        linkedin_url: Optional[str] = None
    ) -> UnifiedCandidateProfile:
        """
        Scrape all platforms for a candidate.
        
        Args:
            candidate_email: Email for generating anonymous ID
            *_url: URLs for each platform (all optional)
            
        Returns:
            UnifiedCandidateProfile with all scraped data
        """
        logger.info("=" * 60)
        logger.info("STARTING UNIFIED SCRAPE")
        logger.info("=" * 60)
        
        # Generate anonymous ID
        candidate_id = self._generate_anonymous_id(candidate_email)
        
        # Initialize profile
        profile = UnifiedCandidateProfile(candidate_id=candidate_id)
        
        # Scrape each platform
        if github_url:
            try:
                profile.github = self._scrape_github(github_url)
            except Exception as e:
                logger.error(f"GitHub scrape failed: {e}")
                profile.scrape_errors["github"] = str(e)
        
        if leetcode_url:
            try:
                profile.leetcode = self._scrape_leetcode(leetcode_url)
            except Exception as e:
                logger.error(f"LeetCode scrape failed: {e}")
                profile.scrape_errors["leetcode"] = str(e)
        
        if codechef_url:
            try:
                profile.codechef = self._scrape_codechef(codechef_url)
            except Exception as e:
                logger.error(f"CodeChef scrape failed: {e}")
                profile.scrape_errors["codechef"] = str(e)
        
        if codeforces_url:
            try:
                profile.codeforces = self._scrape_codeforces(codeforces_url)
            except Exception as e:
                logger.error(f"Codeforces scrape failed: {e}")
                profile.scrape_errors["codeforces"] = str(e)
        
        # Compute aggregates
        profile.compute_aggregates()
        
        logger.info("=" * 60)
        logger.info(f"SCRAPE COMPLETE - Platforms: {profile.platforms_scraped}")
        logger.info("=" * 60)
        
        return profile
    
    def _generate_anonymous_id(self, email: str) -> str:
        """Generate anonymous candidate ID"""
        hash_obj = hashlib.sha256(email.encode())
        return f"anon_{hash_obj.hexdigest()[:8]}"
    
    def _scrape_github(self, url: str) -> GitHubProfile:
        """
        Scrape GitHub profile using API (preferred) or web scraping (fallback).
        
        Uses GitHub API for:
        - Credibility signals (account age, activity)
        - Skill signals (languages, code depth)
        - Consistency signals (commit patterns)
        """
        logger.info(f"Scraping GitHub: {url}")
        
        username = url.rstrip("/").split("/")[-1]
        
        # Try API first (if token available)
        try:
            
            if GITHUB_USE_API and GITHUB_PAT:
                logger.info("Using GitHub API for profile analysis")
                client = GitHubAPIClient(token=GITHUB_PAT)
                api_result = client.analyze_full_profile(username)
                
                if "error" not in api_result:
                    # Convert API result to GitHubProfile
                    profile = api_result.get("profile", {})
                    cred_signal = api_result.get("credibility_signal", {})
                    skill_signal = api_result.get("skill_signal", {})
                    cons_signal = api_result.get("consistency_signal", {})
                    
                    return GitHubProfile(
                        username=username,
                        profile_url=url,
                        
                        # Basic metrics
                        total_commits_last_year=cons_signal.get("commits_last_year", 0),
                        consistency_score=cons_signal.get("score", 50),
                        persona=self._infer_persona(cons_signal),
                        max_gap_days=cons_signal.get("max_gap_days", 0),
                        commits_last_30_days=cons_signal.get("commits_last_30_days", 0),
                        top_languages=skill_signal.get("verified_languages", []),
                        projects=[],  # Will be populated from repo_depths
                        
                        # Credibility signals
                        account_age_years=profile.get("account_age_years", 0),
                        account_created=profile.get("account_created"),
                        credibility_score=cred_signal.get("score", 0),
                        credibility_flags=cred_signal.get("flags", []),
                        has_bio=profile.get("has_bio", False),
                        has_company=profile.get("has_company", False),
                        followers=profile.get("followers", 0),
                        public_repos=profile.get("public_repos", 0),
                        
                        # Skill signals
                        primary_language=skill_signal.get("primary_language"),
                        language_distribution=skill_signal.get("language_distribution", {}),
                        verified_languages=skill_signal.get("verified_languages", []),
                        avg_code_depth=skill_signal.get("avg_code_depth", 0),
                        repo_depths=skill_signal.get("top_repo_depths", []),
                        
                        # Activity patterns
                        active_weeks_ratio=cons_signal.get("active_weeks_ratio", 0),
                        days_since_last_commit=cons_signal.get("days_since_last_commit"),
                        activity_patterns=cons_signal.get("patterns", []),
                        
                        scraped_at=datetime.now().isoformat(),
                        data_source="api"
                    )
                else:
                    logger.warning(f"API error: {api_result.get('error')}, falling back to scraping")
            
        except Exception as e:
            logger.warning(f"GitHub API failed, falling back to scraping: {e}")
        
        # Fallback: Web scraping
        logger.info("Using web scraping for GitHub profile")
        raw_html = scrape_website(url)
        
        # Get contribution stats
        stats = get_contribution_history(raw_html)
        header_count = get_contribution_count(raw_html)
        
        # Parse header count
        total_commits = 0
        if "contributions" in str(header_count):
            import re
            match = re.search(r"([\d,]+)", str(header_count))
            if match:
                total_commits = int(match.group(1).replace(",", ""))
        
        # Analyze consistency with LLM
        consistency_result = self.parser.parse_github_consistency(stats)
        
        # Get project details (top 3 repos)
        projects = []
        try:
            # Get repos from page
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "html.parser")
            repo_links = soup.find_all("a", {"itemprop": "name codeRepository"})[:3]
            
            for link in repo_links:
                repo_url = f"https://github.com{link.get('href', '')}"
                details = get_project_details(repo_url)
                projects.append({
                    "name": link.get_text(strip=True),
                    "url": repo_url,
                    "languages": details.get("languages", []),
                    "readme_snippet": details.get("readme_snippet", "")[:200]
                })
        except Exception as e:
            logger.warning(f"Could not get project details: {e}")
        
        return GitHubProfile(
            username=username,
            profile_url=url,
            total_commits_last_year=total_commits,
            consistency_score=consistency_result.get("consistency_score", 5) * 10,  # Scale to 0-100
            persona=consistency_result.get("persona", "Unknown"),
            max_gap_days=stats.get("max_gap", 0),
            commits_last_30_days=stats.get("commits_last_30_days", 0),
            top_languages=stats.get("top_languages", []),
            projects=projects,
            monthly_log=stats.get("monthly_log", {}),
            scraped_at=datetime.now().isoformat(),
            data_source="scrape"
        )
    
    def _infer_persona(self, consistency_signal: Dict) -> str:
        """Infer persona from consistency signal patterns"""
        patterns = consistency_signal.get("patterns", [])
        score = consistency_signal.get("score", 0)
        
        if "consistent_contributor" in patterns:
            return "Veteran"
        elif score >= 70:
            return "Recently active"
        elif "long_inactivity_gaps" in patterns:
            return "Burnout"
        elif "burst_activity" in patterns:
            return "Sporadic"
        else:
            return "Unknown"

    
    def _scrape_leetcode(self, url: str) -> LeetCodeProfile:
        """Scrape LeetCode profile"""
        logger.info(f"Scraping LeetCode: {url}")
        
        username = url.rstrip("/").split("/")[-1]
        
        # Scrape with dynamic page handler
        result = scrape_dynamic_page(url, "LeetCode")
        
        if "error" in result:
            raise Exception(result["error"])
        
        raw_text = result.get("content", "")
        
        # Parse with LLM
        parsed = self.parser.parse_platform(raw_text, "LeetCode")
        
        # Build profile
        difficulty = parsed.get("difficulty_breakdown", {})
        
        return LeetCodeProfile(
            username=username,
            profile_url=url,
            rank=parsed.get("rank", "Unrated"),
            problems_solved=int(parsed.get("problems_solved") or 0),
            difficulty_breakdown={
                "easy": int(difficulty.get("easy") or 0),
                "medium": int(difficulty.get("medium") or 0),
                "hard": int(difficulty.get("hard") or 0)
            },
            contest_rating=parsed.get("contest_rating") if parsed.get("contest_rating") else None,
            max_rating=int(parsed["max_rating"]) if parsed.get("max_rating") and parsed.get("max_rating") != "null" else None,
            top_language=parsed.get("top_language", "Unknown"),
            top_skills=parsed.get("top_skills", []),
            badges=int(parsed.get("badges") or 0),
            scraped_at=datetime.now().isoformat()
        )
    
    def _scrape_codechef(self, url: str) -> CodeChefProfile:
        """Scrape CodeChef profile"""
        logger.info(f"Scraping CodeChef: {url}")
        
        username = url.rstrip("/").split("/")[-1]
        
        # Scrape with dynamic page handler
        result = scrape_dynamic_page(url, "CodeChef")
        
        if "error" in result:
            raise Exception(result["error"])
        
        raw_text = result.get("content", "")
        
        # Parse with LLM
        parsed = self.parser.parse_platform(raw_text, "CodeChef")
        
        # Extract rating from contest_rating string
        rating = 0
        stars = 0
        contest_str = str(parsed.get("contest_rating", ""))
        import re
        rating_match = re.search(r"(\d+)", contest_str)
        if rating_match:
            rating = int(rating_match.group(1))
        star_match = re.search(r"(\d+)★", contest_str)
        if star_match:
            stars = int(star_match.group(1))
        
        return CodeChefProfile(
            username=username,
            profile_url=url,
            rank=str(parsed.get("rank", "Unrated")),
            rating=rating,
            stars=parsed.get("stars", stars),
            max_rating=int(parsed["max_rating"]) if parsed.get("max_rating") else None,
            problems_solved=int(parsed.get("problems_solved", 0)),
            top_language=str(parsed.get("top_language", "Unknown")),
            top_skills=parsed.get("top_skills", []),
            badges=int(parsed.get("badges", 0)),
            scraped_at=datetime.now().isoformat()
        )
    
    def _scrape_codeforces(self, url: str) -> CodeforcesProfile:
        """Scrape Codeforces profile"""
        logger.info(f"Scraping Codeforces: {url}")
        
        username = url.rstrip("/").split("/")[-1]
        
        # Scrape with dynamic page handler
        result = scrape_dynamic_page(url, "Codeforces")
        
        if "error" in result:
            raise Exception(result["error"])
        
        raw_text = result.get("content", "")
        
        # Parse with LLM
        parsed = self.parser.parse_platform(raw_text, "Codeforces")
        
        return CodeforcesProfile(
            username=username,
            profile_url=url,
            rank=str(parsed.get("rank", "Unrated")),
            contest_rating=int(parsed["contest_rating"]) if parsed.get("contest_rating") else None,
            max_rating=int(parsed["max_rating"]) if parsed.get("max_rating") else None,
            problems_solved=int(parsed.get("problems_solved", 0)),
            top_language=str(parsed.get("top_language", "Unknown")),
            top_skills=parsed.get("top_skills", []),
            badges=int(parsed.get("badges", 0)),
            scraped_at=datetime.now().isoformat()
        )
    
    def save_profile(self, profile: UnifiedCandidateProfile, output_dir: str = ".") -> str:
        """
        Save profile to JSON file.
        
        Args:
            profile: Unified profile
            output_dir: Directory to save to
            
        Returns:
            Path to saved file
        """
        filename = f"{profile.candidate_id}_profile.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(profile.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Profile saved to: {filepath}")
        return filepath


# Convenience function for quick scraping
def scrape_candidate(
    email: str,
    github_url: str = None,
    leetcode_url: str = None,
    codechef_url: str = None,
    codeforces_url: str = None,
    llm_backend: str = "ollama"
) -> Dict:
    """
    Quick function to scrape a candidate and return dict.
    
    Args:
        email: Candidate email for ID generation
        *_url: Platform URLs
        llm_backend: "ollama" or "openrouter"
        
    Returns:
        Unified profile as dictionary
    """
    scraper = UnifiedScraper(llm_backend=llm_backend)
    profile = scraper.scrape_candidate(
        candidate_email=email,
        github_url=github_url,
        leetcode_url=leetcode_url,
        codechef_url=codechef_url,
        codeforces_url=codeforces_url
    )
    return profile.model_dump()


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("UNIFIED SCRAPER TEST")
    print("=" * 60)
    
    # Test with sample URLs (replace with real profiles)
    result = scrape_candidate(
        email="test@example.com",
        github_url="https://github.com/torvalds",
        # leetcode_url="https://leetcode.com/uwi",
        llm_backend="ollama"
    )
    
    print(json.dumps(result, indent=2, default=str))
