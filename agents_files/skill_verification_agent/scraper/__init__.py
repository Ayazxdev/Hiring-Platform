"""
Scraper Package

Unified scraper for multi-platform profile data extraction.
"""
from .unified_scraper import UnifiedScraper, scrape_candidate
from .scrape import (
    identify_platform,
    scrape_website,
    scrape_dynamic_page,
    get_contribution_history,
    get_contribution_count,
    get_project_details
)
from .parse import ProfileParser, parse_with_ollama
from .schemas import (
    UnifiedCandidateProfile,
    GitHubProfile,
    LeetCodeProfile,
    CodeChefProfile,
    CodeforcesProfile
)

__all__ = [
    # Main entry points
    "UnifiedScraper",
    "scrape_candidate",
    
    # Parser
    "ProfileParser",
    "parse_with_ollama",
    
    # Scrapers
    "identify_platform",
    "scrape_website",
    "scrape_dynamic_page",
    "get_contribution_history",
    "get_contribution_count",
    "get_project_details",
    
    # Schemas
    "UnifiedCandidateProfile",
    "GitHubProfile",
    "LeetCodeProfile",
    "CodeChefProfile",
    "CodeforcesProfile"
]
