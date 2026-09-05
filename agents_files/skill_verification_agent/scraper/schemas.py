"""
Pydantic Schemas for Unified Profile Data

These schemas define the structure of the JSON output from the scraper.
One JSON file per candidate, containing all platform data.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DifficultyBreakdown(BaseModel):
    """LeetCode/CodeChef difficulty breakdown"""
    easy: int = 0
    medium: int = 0
    hard: int = 0


class GitHubProfile(BaseModel):
    """Normalized GitHub profile data (API-enhanced)"""
    username: str
    profile_url: str
    
    # Basic metrics
    total_commits_last_year: int = 0
    consistency_score: int = Field(0, ge=0, le=100, description="0-100 consistency score")
    persona: str = Field("Unknown", description="Veteran/Recently active/Burnout/Sporadic/Inactive")
    max_gap_days: int = 0
    commits_last_30_days: int = 0
    top_languages: List[str] = []
    projects: List[Dict[str, Any]] = []
    monthly_log: Dict[str, int] = {}
    
    # NEW: Credibility signals (from API)
    account_age_years: float = 0
    account_created: Optional[str] = None
    credibility_score: int = 0
    credibility_flags: List[str] = []
    has_bio: bool = False
    has_company: bool = False
    followers: int = 0
    public_repos: int = 0
    
    # NEW: Skill signals (from API)
    primary_language: Optional[str] = None
    language_distribution: Dict[str, float] = {}
    verified_languages: List[str] = []
    avg_code_depth: float = 0
    repo_depths: List[Dict[str, Any]] = []
    
    # NEW: Activity patterns
    active_weeks_ratio: float = 0
    days_since_last_commit: Optional[int] = None
    activity_patterns: List[str] = []  # weekend_only, burst_activity, consistent, etc.
    
    # Metadata
    scraped_at: Optional[str] = None
    data_source: str = "api"  # "api" or "scrape"


class LeetCodeProfile(BaseModel):
    """Normalized LeetCode profile data"""
    username: str
    profile_url: str
    rank: str = "Unrated"
    problems_solved: int = 0
    difficulty_breakdown: DifficultyBreakdown = DifficultyBreakdown()
    contest_rating: Optional[str] = None
    max_rating: Optional[int] = None
    top_language: str = "Unknown"
    top_skills: List[str] = []
    badges: int = 0
    scraped_at: Optional[str] = None


class CodeChefProfile(BaseModel):
    """Normalized CodeChef profile data"""
    username: str
    profile_url: str
    rank: str = "Unrated"
    rating: int = 0
    stars: int = 0
    max_rating: Optional[int] = None
    problems_solved: int = 0
    top_language: str = "Unknown"
    top_skills: List[str] = []
    badges: int = 0
    scraped_at: Optional[str] = None


class CodeforcesProfile(BaseModel):
    """Normalized Codeforces profile data"""
    username: str
    profile_url: str
    rank: str = "Unrated"
    contest_rating: Optional[int] = None
    max_rating: Optional[int] = None
    problems_solved: int = 0
    top_language: str = "Unknown"
    top_skills: List[str] = []
    badges: int = 0
    scraped_at: Optional[str] = None


class LinkedInProfile(BaseModel):
    """Normalized LinkedIn profile data"""
    profile_url: str
    headline: Optional[str] = None
    years_experience: int = 0
    current_company: Optional[str] = None
    top_skills: List[str] = []
    education: Optional[str] = None
    scraped_at: Optional[str] = None


class UnifiedCandidateProfile(BaseModel):
    """
    Complete unified profile for one candidate.
    
    This is the final output format - ONE JSON per candidate.
    Contains data from all scraped platforms.
    """
    candidate_id: str = Field(..., description="Anonymous candidate identifier")
    
    # Platform profiles (all optional - candidate may not have all platforms)
    github: Optional[GitHubProfile] = None
    leetcode: Optional[LeetCodeProfile] = None
    codechef: Optional[CodeChefProfile] = None
    codeforces: Optional[CodeforcesProfile] = None
    linkedin: Optional[LinkedInProfile] = None
    
    # Metadata
    scraped_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    platforms_scraped: List[str] = []
    scrape_errors: Dict[str, str] = {}  # platform -> error message
    
    # Aggregated metrics (computed after scraping)
    total_problems_solved: int = 0
    best_contest_rating: Optional[int] = None
    primary_language: str = "Unknown"
    all_skills: List[str] = []
    
    def compute_aggregates(self):
        """Compute aggregated metrics from all platforms"""
        self.platforms_scraped = []
        problems_total = 0
        best_rating = None
        languages = []
        skills = set()
        
        if self.github:
            self.platforms_scraped.append("github")
            languages.extend(self.github.top_languages)
        
        if self.leetcode:
            self.platforms_scraped.append("leetcode")
            problems_total += self.leetcode.problems_solved
            if self.leetcode.max_rating:
                if best_rating is None or self.leetcode.max_rating > best_rating:
                    best_rating = self.leetcode.max_rating
            if self.leetcode.top_language != "Unknown":
                languages.append(self.leetcode.top_language)
            skills.update(self.leetcode.top_skills)
        
        if self.codechef:
            self.platforms_scraped.append("codechef")
            problems_total += self.codechef.problems_solved
            if self.codechef.max_rating:
                if best_rating is None or self.codechef.max_rating > best_rating:
                    best_rating = self.codechef.max_rating
            if self.codechef.top_language != "Unknown":
                languages.append(self.codechef.top_language)
            skills.update(self.codechef.top_skills)
        
        if self.codeforces:
            self.platforms_scraped.append("codeforces")
            problems_total += self.codeforces.problems_solved
            if self.codeforces.max_rating:
                if best_rating is None or self.codeforces.max_rating > best_rating:
                    best_rating = self.codeforces.max_rating
            if self.codeforces.top_language != "Unknown":
                languages.append(self.codeforces.top_language)
            skills.update(self.codeforces.top_skills)
        
        if self.linkedin:
            self.platforms_scraped.append("linkedin")
            skills.update(self.linkedin.top_skills)
        
        self.total_problems_solved = problems_total
        self.best_contest_rating = best_rating
        self.all_skills = list(skills)
        
        # Find primary language (most common)
        if languages:
            from collections import Counter
            self.primary_language = Counter(languages).most_common(1)[0][0]
    
    def to_agent_format(self) -> Dict[str, Any]:
        """
        Convert to format expected by SkillVerificationAgent.
        
        Returns:
            Dict matching the expected scraper output format
        """
        result = {}
        
        if self.github:
            result["github_data"] = {
                "source": "github",
                "data": {
                    "total_commits_last_year": self.github.total_commits_last_year,
                    "consistency_score": self.github.consistency_score * 10,  # Scale to 0-100
                    "projects": self.github.projects,
                    "top_languages": self.github.top_languages,
                    "monthly_log": self.github.monthly_log,
                    "max_gap": self.github.max_gap_days
                }
            }
        
        if self.leetcode:
            result["leetcode_data"] = {
                "source": "leetcode",
                "data": {
                    "rank": self.leetcode.rank,
                    "problems_solved": self.leetcode.problems_solved,
                    "difficulty_breakdown": self.leetcode.difficulty_breakdown.model_dump(),
                    "contest_rating": self.leetcode.contest_rating or "Unrated",
                    "max_rating": self.leetcode.max_rating,
                    "top_language": self.leetcode.top_language,
                    "top_skills": self.leetcode.top_skills,
                    "badges": self.leetcode.badges
                }
            }
        
        if self.codechef:
            result["codechef_data"] = {
                "source": "codechef",
                "data": {
                    "rank": self.codechef.rank,
                    "rating": self.codechef.rating,
                    "problems_solved": self.codechef.problems_solved,
                    "top_language": self.codechef.top_language,
                    "top_skills": self.codechef.top_skills,
                    "badges": self.codechef.badges,
                    "max_rating": self.codechef.max_rating
                }
            }
        
        return result
