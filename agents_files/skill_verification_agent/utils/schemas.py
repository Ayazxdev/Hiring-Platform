"""
Pydantic schemas for type safety and validation
"""
from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime


class GitHubProject(BaseModel):
    """Schema for individual GitHub project"""
    name: str
    readme_analysis: Dict[str, Any]
    code_quality: str
    project_score: int = Field(ge=0, le=100)


class GitHubData(BaseModel):
    """Normalized GitHub data"""
    total_commits_last_year: int
    monthly_activity: Dict[str, int]
    projects: List[GitHubProject]
    top_languages: List[str]
    consistency_score: int = Field(ge=0, le=100)


class LeetCodeData(BaseModel):
    """Normalized LeetCode data"""
    rank: str
    problems_solved: int
    contest_rating: Optional[str]
    max_rating: Optional[int]
    top_skills: List[str]
    top_language: str
    badges: int
    difficulty_breakdown: Dict[str, int]


class CodeChefData(BaseModel):
    """Normalized CodeChef data"""
    rating: int
    problems_solved: int
    contest_rating: Optional[int]
    top_language: str


class NormalizedEvidence(BaseModel):
    """Unified evidence schema"""
    github: Optional[Dict[str, Any]] = None
    leetcode: Optional[Dict[str, Any]] = None
    codechef: Optional[Dict[str, Any]] = None


class SkillCredential(BaseModel):
    """Final skill verification output"""
    candidate_id: str
    verified_skills: List[str]
    skill_confidence: int = Field(ge=0, le=100)
    evidence: Dict[str, Any]
    evidence_details: Dict[str, Any]
    manipulation_detected: bool
    signal_strength: Literal["strong", "weak"]
    credential_id: str
    issued_at: str = Field(default_factory=lambda: datetime.now().isoformat())
