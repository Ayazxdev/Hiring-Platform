"""
GitHub API Integration for Skill Verification Agent

Uses GitHub REST API to extract:
1. Credibility signals (account age, activity patterns)
2. Skill signals (languages, code depth)
3. Consistency signals (commit timelines, ownership)

Based on 2026 hiring research - behavioral signals > volume metrics.
"""
import os
import sys
import json
import logging
import requests
import base64
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict

# Handle imports for both module and standalone usage
try:
    from .framework_detector import FrameworkDetector
    from learning.github_skill_learner import GithubSkillLearner
    from learning.ontology_updater import OntologyUpdater
except (ImportError, ModuleNotFoundError):
    # Running as standalone script or in sub-module
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scraper.framework_detector import FrameworkDetector
    from learning.github_skill_learner import GithubSkillLearner
    from learning.ontology_updater import OntologyUpdater

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """
    GitHub API client for deep profile analysis.
    
    Extracts signals that ATS cannot see:
    - Account credibility (age, activity consistency)
    - Skill verification (language dominance, code depth)
    - Behavioral patterns (commit timing, ownership)
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str = None):
        """
        Initialize with GitHub PAT token.
        
        Args:
            token: GitHub Personal Access Token (from config or param)
        """
        self.token = token or os.getenv("GITHUB_PAT")
        
        if not self.token:
            logger.warning("No GitHub token provided - rate limits will apply (60 req/hour)")
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SkillVerificationAgent/1.0"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
            logger.info("GitHub API initialized with authentication")
        
        self.rate_limit_remaining = None
        self.framework_detector = FrameworkDetector()
        
        # Auto-Learning Engine
        self.skill_learner = GithubSkillLearner()
        # Ensure ontology path is correct ( sibling to scraper/ )
        ontology_path = Path(__file__).parent.parent / "knowledge" / "skill_ontology.json"
        self.ontology_updater = OntologyUpdater(str(ontology_path))
    
    
    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to GitHub API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            # Track rate limit
            self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                # Expected for optional resources (e.g., .github/workflows)
                logger.debug(f"Resource not found: {endpoint}")
                return None
            elif response.status_code == 403:
                logger.error(f"Rate limit exceeded or forbidden: {response.text}")
                return None
            else:
                logger.error(f"GitHub API error {response.status_code}: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    
    def get_file_content(self, repo_full_name: str, file_path: str, max_lines: int = 20) -> Optional[str]:
        """
        Fetch file content from GitHub (first N lines only for performance).
        
        Args:
            repo_full_name: Full repo name (username/repo)
            file_path: Path to file in repo
            max_lines: Maximum number of lines to fetch (default: 20)
        
        Returns:
            File content (first N lines) or None
        """
        endpoint = f"/repos/{repo_full_name}/contents/{file_path}"
        response = self._request(endpoint)
        
        if not response:
            return None
        
        try:
            if response.get("encoding") == "base64":
                content = base64.b64decode(response["content"]).decode('utf-8', errors='ignore')
                # Return only first N lines
                return "\n".join(content.splitlines()[:max_lines])
        except Exception as e:
            logger.debug(f"Failed to decode file {file_path}: {e}")
        
        return None
    
    
    def scan_repo_for_frameworks(self, repo_full_name: str, language: str) -> Dict:
        """
        Scan repository for framework usage via imports and dependencies.
        
        Args:
            repo_full_name: Full repo name (username/repo)
            language: Primary language of repo
        
        Returns:
            Dict with detected frameworks (confidence-based) and evidence
        """
        # Track evidence per skill
        skill_evidence = {}  # {skill_name: {confidence, evidence_type, files: set()}}
        
        # Step 1: Check dependency files (Python, Node/TS, Go, Rust)
        dep_checks = [
            ("requirements.txt", "Python"),
            ("pyproject.toml", "Python"),
            ("setup.py", "Python"),
            ("package.json", "JavaScript")
        ]
        
        for dep_file, dep_lang in dep_checks:
            content = self.get_file_content(repo_full_name, dep_file, max_lines=150)
            if content:
                frameworks = self.framework_detector.scan_dependencies(content, dep_lang)
                if frameworks:
                    for fw in frameworks:
                        if fw not in skill_evidence:
                            skill_evidence[fw] = {
                                "skill": fw,
                                "confidence": "high",
                                "evidence_type": "dependency",
                                "reason": f"Listed in {dep_file}",
                                "files": set()
                            }
                        skill_evidence[fw]["files"].add(dep_file)
        
        # Step 2: Scan code files (first 20 lines only)
        # Get repo file tree - REMOVED recursive=1 for performance
        tree = self._request(f"/repos/{repo_full_name}/git/trees/main")
        if not tree or not tree.get("tree"):
            tree = self._request(f"/repos/{repo_full_name}/git/trees/master")
        
        if tree and tree.get("tree"):
            files = tree["tree"]
            scanned_count = 0
            
            # Sub-directories to peek into if they exist
            PEEK_DIRS = ["src", "app", "include", "lib", "scripts"]
            all_files = list(files)
            
            # Lightweight addition: check root + immediate subdirs above
            for item in files:
                if item["type"] == "tree" and item["path"] in PEEK_DIRS:
                    try:
                        sub_tree = self._request(f"/repos/{repo_full_name}/git/trees/{item['sha']}")
                        if sub_tree and sub_tree.get("tree"):
                            for sub_item in sub_tree["tree"]:
                                sub_item["path"] = f"{item['path']}/{sub_item['path']}"
                                all_files.append(sub_item)
                    except Exception:
                        pass

            # Step 2a: Check configuration and containerization artifacts
            for item in all_files:
                f_path = item.get("path", "")
                f_base = os.path.basename(f_path).lower()
                
                # Docker detection
                if f_base.startswith("dockerfile") or f_base in ["docker-compose.yml", "docker-compose.yaml", "compose.yaml"]:
                    if "Docker" not in skill_evidence:
                        skill_evidence["Docker"] = {
                            "skill": "Docker",
                            "confidence": "high",
                            "evidence_type": "configuration",
                            "reason": f"Containerized environment in {f_path}",
                            "files": set()
                        }
                    skill_evidence["Docker"]["files"].add(f_path)
                
                # Tailwind CSS configuration detection
                if f_base.startswith("tailwind.config"):
                    if "Tailwind CSS" not in skill_evidence:
                        skill_evidence["Tailwind CSS"] = {
                            "skill": "Tailwind CSS",
                            "confidence": "high",
                            "evidence_type": "configuration",
                            "reason": f"Tailwind configuration in {f_path}",
                            "files": set()
                        }
                    skill_evidence["Tailwind CSS"]["files"].add(f_path)

            for file in all_files:
                if file["type"] != "blob" or scanned_count >= 15:  # Reduced from 50
                    continue
                
                # Detect language from extension
                file_lang = self.framework_detector.infer_language(file["path"])
                if not file_lang or file_lang != language:
                    continue
                
                # Fetch and scan file
                content = self.get_file_content(repo_full_name, file["path"], max_lines=20)
                if content:
                    imports = self.framework_detector.scan_file_for_imports(content, language)
                    if imports:
                        detected = self.framework_detector.detect_frameworks(imports, language)
                        if detected:
                            for detection in detected:
                                skill = detection["skill"]
                                
                                # If not seen before, add it
                                if skill not in skill_evidence:
                                    skill_evidence[skill] = {
                                        "skill": skill,
                                        "confidence": detection["confidence"],
                                        "evidence_type": detection["evidence_type"],
                                        "reason": detection["reason"],
                                        "files": set()
                                    }
                                else:
                                    # Upgrade confidence if we see higher evidence
                                    if detection["confidence"] == "high" and skill_evidence[skill]["confidence"] == "low":
                                        skill_evidence[skill]["confidence"] = "high"
                                        skill_evidence[skill]["evidence_type"] = detection["evidence_type"]
                                        skill_evidence[skill]["reason"] = detection["reason"]
                                
                                # Track file
                                skill_evidence[skill]["files"].add(file["path"])
                            
                            scanned_count += 1
                            
                            # --- NEW: Auto-Learning Integration ---
                            # Extract all raw imports for the learner
                            raw_imports = self.skill_learner.extract_imports(content, language)
                            # Map to framework candidates
                            framework_candidates = self.skill_learner.detect_framework_candidates(raw_imports)
                            # Get the current ontology (cached state)
                            # For simplicity we load it inside the updater
                            ontology = self.ontology_updater.load_ontology()
                            # Filter for new ones
                            new_frameworks = self.skill_learner.filter_new_frameworks(framework_candidates, ontology)
                            
                            if new_frameworks:
                                # Auto-update the ontology
                                self.ontology_updater.update_with_new_frameworks(new_frameworks, language)
                                
                            if scanned_count >= 15: break
        
        # Convert to final format
        detections = []
        for skill_data in skill_evidence.values():
            detections.append({
                "skill": skill_data["skill"],
                "confidence": skill_data["confidence"],
                "confidence_score": 1.0 if skill_data["confidence"] == "high" else 0.3,
                "evidence_type": skill_data["evidence_type"],
                "reason": skill_data["reason"],
                "files": sorted(list(skill_data["files"]))[:5]  # Top 5 files per skill
            })
        
        return {
            "detections": detections,
            "scan_method": "import_analysis + dependency_parsing"
        }

    
    
    # USER-LEVEL CREDIBILITY SIGNALS
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """
        Get user profile with credibility signals.
        
        Returns:
            - Account age
            - Bio/headline
            - Follower metrics
            - Public repo count
            - Activity recency
        """
        user = self._request(f"/users/{username}")
        
        if not user:
            return None
        
        created_at = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
        account_age_days = (datetime.now(created_at.tzinfo) - created_at).days
        account_age_years = round(account_age_days / 365, 1)
        
        # Updated recently?
        updated_at = datetime.fromisoformat(user["updated_at"].replace("Z", "+00:00"))
        days_since_update = (datetime.now(updated_at.tzinfo) - updated_at).days
        
        return {
            "username": user["login"],
            "name": user.get("name"),
            "bio": user.get("bio"),
            "company": user.get("company"),
            "location": user.get("location"),
            "email": user.get("email"),  # Only if public
            "blog": user.get("blog"),
            
            # Credibility metrics
            "account_created": user["created_at"],
            "account_age_years": account_age_years,
            "account_age_days": account_age_days,
            
            # Activity metrics
            "public_repos": user.get("public_repos", 0),
            "public_gists": user.get("public_gists", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "days_since_update": days_since_update,
            
            # Credibility flags
            "is_hireable": user.get("hireable", False),
            "has_bio": bool(user.get("bio")),
            "has_company": bool(user.get("company")),
            "has_blog": bool(user.get("blog")),
            
            # Avatar (for UI)
            "avatar_url": user.get("avatar_url"),
            "profile_url": user.get("html_url")
        }
    
    
    def calculate_credibility_score(self, user_data: Dict) -> Dict:
        """
        Calculate credibility score from user profile.
        
        Scoring:
        - Account age > 2 years: +30
        - Has bio: +10
        - Has company: +10
        - Followers > 10: +10
        - Active recently (< 30 days): +20
        - Multiple repos (> 5): +20
        
        Red flags:
        - Account < 6 months + many claims: 🚩
        - No bio, no followers, sudden repos: 🚩
        """
        score = 0
        flags = []
        
        # Account age (VERY important)
        age_years = user_data.get("account_age_years", 0)
        if age_years >= 3:
            score += 30
        elif age_years >= 1:
            score += 20
        elif age_years >= 0.5:
            score += 10
        else:
            flags.append("new_account_under_6_months")
        
        # Profile completeness
        if user_data.get("has_bio"):
            score += 10
        if user_data.get("has_company"):
            score += 10
        if user_data.get("has_blog"):
            score += 5
        
        # Follower credibility (mild weight)
        followers = user_data.get("followers", 0)
        if followers >= 50:
            score += 15
        elif followers >= 10:
            score += 10
        elif followers >= 5:
            score += 5
        
        # Activity recency
        days_since_update = user_data.get("days_since_update", 999)
        if days_since_update <= 7:
            score += 20
        elif days_since_update <= 30:
            score += 15
        elif days_since_update <= 90:
            score += 10
        else:
            flags.append("inactive_over_90_days")
        
        # Repo count (basic)
        repos = user_data.get("public_repos", 0)
        if repos >= 10:
            score += 15
        elif repos >= 5:
            score += 10
        
        # Red flag detection
        if age_years < 0.5 and repos > 20:
            flags.append("new_account_suspicious_repo_count")
        
        if not user_data.get("has_bio") and followers < 5 and repos > 10:
            flags.append("empty_profile_many_repos")
        
        return {
            "credibility_score": min(100, score),
            "flags": flags,
            "breakdown": {
                "account_age": age_years,
                "profile_complete": user_data.get("has_bio") and user_data.get("has_company"),
                "followers": followers,
                "recent_activity": days_since_update <= 30,
                "repo_count": repos
            }
        }
    
    
    # LANGUAGE & SKILL SIGNALS
    
    def get_user_repos(self, username: str, max_repos: int = 30) -> List[Dict]:
        """
        Get user's repositories for language analysis.
        
        Returns list of repos with metadata.
        """
        repos = self._request(
            f"/users/{username}/repos",
            params={"per_page": max_repos, "sort": "updated", "type": "owner"}
        )
        
        if not repos:
            return []
        
        return [
            {
                "name": repo["name"],
                "url": repo["html_url"],
                "description": repo.get("description"),
                "language": repo.get("language"),
                "is_fork": repo.get("fork", False),
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "pushed_at": repo.get("pushed_at"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "size": repo.get("size", 0),
                "has_issues": repo.get("has_issues", False),
                "has_wiki": repo.get("has_wiki", False),
                "topics": repo.get("topics", []),
                "default_branch": repo.get("default_branch", "main")
            }
            for repo in repos
        ]
    
    
    def aggregate_languages(self, username: str, repos: List[Dict] = None) -> Dict:
        """
        Aggregate languages across all repos.
        
        Returns:
            - Primary language
            - Language distribution
            - Skill verification (Python claimed → Python repos?)
        """
        if repos is None:
            repos = self.get_user_repos(username)
        
        # Count languages (exclude forks by default)
        language_counts = Counter()
        language_bytes = defaultdict(int)
        
        original_repos = [r for r in repos if not r.get("is_fork")]
        
        for repo in original_repos:
            lang = repo.get("language")
            if lang:
                language_counts[lang] += 1
                
                # Get detailed language breakdown for this repo
                repo_languages = self._request(f"/repos/{username}/{repo['name']}/languages")
                
                if repo_languages:
                    for lang_name, bytes_count in repo_languages.items():
                        language_bytes[lang_name] += bytes_count
                else:
                    # FALLBACK: If API rate limited or failed, use primary language
                    # Assume average repo size (or use size if available)
                    # This prevents "empty skills" when API limits are hit without a token.
                    logger.warning(f"Could not fetch languages for {repo['name']}, using primary language fallback: {lang}")
                    fallback_size = repo.get("size", 1000) * 1024 # size is in KB
                    language_bytes[lang] += fallback_size

        # Calculate distribution
        total_bytes = sum(language_bytes.values()) or 1
        language_distribution = {
            lang: round(bytes_count / total_bytes * 100, 1)
            for lang, bytes_count in sorted(language_bytes.items(), key=lambda x: -x[1])
        }
        
        # Primary language (>= 40% of code)
        primary_language = None
        for lang, pct in language_distribution.items():
            if pct >= 40:
                primary_language = lang
                break
        
        return {
            "primary_language": primary_language,
            "languages_by_repo_count": dict(language_counts.most_common(10)),
            "languages_by_bytes": language_distribution,
            "total_languages": len(language_counts),
            "original_repos_analyzed": len(original_repos),
            
            # Skill signals
            "verified_languages": [
                lang for lang, pct in language_distribution.items() if pct >= 10
            ]
        }
    
    
    # COMMIT HISTORY & CONSISTENCY
    
    def get_commit_activity(self, username: str, repos: List[Dict] = None) -> Dict:
        """
        Analyze commit patterns across repos.
        
        Detects:
        - Regular consistent commits
        - Burst-only activity (exam cramming)
        - Weekend-only patterns
        - Long inactivity gaps
        """
        if repos is None:
            repos = self.get_user_repos(username, max_repos=10)
        
        all_commits = []
        commit_dates = []
        
        for repo in repos[:10]:  # Limit to avoid rate limiting
            # Get commit history
            commits = self._request(
                f"/repos/{username}/{repo['name']}/commits",
                params={"author": username, "per_page": 100}
            )
            
            if commits:
                for commit in commits:
                    commit_date = commit.get("commit", {}).get("author", {}).get("date")
                    if commit_date:
                        dt = datetime.fromisoformat(commit_date.replace("Z", "+00:00"))
                        commit_dates.append(dt)
                        all_commits.append({
                            "repo": repo["name"],
                            "date": dt,
                            "message": commit.get("commit", {}).get("message", "")[:100],
                            "day_of_week": dt.weekday()
                        })
        
        if not commit_dates:
            return {"error": "No commits found", "commit_count": 0}
        
        # Sort by date
        commit_dates.sort()
        
        # Calculate metrics
        now = datetime.now(commit_dates[0].tzinfo)
        last_year = now - timedelta(days=365)
        last_30_days = now - timedelta(days=30)
        last_90_days = now - timedelta(days=90)
        
        commits_last_year = [d for d in commit_dates if d >= last_year]
        commits_last_30 = [d for d in commit_dates if d >= last_30_days]
        commits_last_90 = [d for d in commit_dates if d >= last_90_days]
        
        # Calculate gaps
        gaps = []
        for i in range(1, len(commit_dates)):
            gap = (commit_dates[i] - commit_dates[i-1]).days
            gaps.append(gap)
        
        max_gap = max(gaps) if gaps else 0
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        # Day of week distribution (detect weekend-only)
        day_distribution = Counter(c["day_of_week"] for c in all_commits)
        weekend_commits = day_distribution.get(5, 0) + day_distribution.get(6, 0)
        weekday_commits = sum(day_distribution.get(d, 0) for d in range(5))
        
        # Detect burst patterns
        # Group commits by week
        weekly_commits = defaultdict(int)
        for d in commit_dates:
            week_key = d.isocalendar()[:2]  # (year, week)
            weekly_commits[week_key] += 1
        
        weeks_with_commits = len(weekly_commits)
        total_weeks = 52  # Last year
        active_weeks_ratio = weeks_with_commits / total_weeks
        
        # Detect patterns
        patterns = []
        if weekday_commits == 0 and weekend_commits > 10:
            patterns.append("weekend_only")
        if max_gap > 60:
            patterns.append("long_inactivity_gaps")
        if active_weeks_ratio < 0.2 and len(commits_last_year) > 50:
            patterns.append("burst_activity")
        if active_weeks_ratio > 0.5:
            patterns.append("consistent_contributor")
        
        return {
            "total_commits_analyzed": len(all_commits),
            "commits_last_30_days": len(commits_last_30),
            "commits_last_90_days": len(commits_last_90),
            "commits_last_year": len(commits_last_year),
            
            # Gap analysis
            "max_gap_days": max_gap,
            "avg_gap_days": round(avg_gap, 1),
            
            # Day distribution
            "weekend_commits_pct": round(weekend_commits / len(all_commits) * 100, 1) if all_commits else 0,
            "weekday_commits_pct": round(weekday_commits / len(all_commits) * 100, 1) if all_commits else 0,
            
            # Consistency
            "active_weeks_ratio": round(active_weeks_ratio, 2),
            "weeks_with_commits": weeks_with_commits,
            
            # Patterns
            "patterns": patterns,
            
            # First/last commit
            "first_commit": commit_dates[0].isoformat() if commit_dates else None,
            "last_commit": commit_dates[-1].isoformat() if commit_dates else None,
            "days_since_last_commit": (now - commit_dates[-1]).days if commit_dates else None
        }
    
    
    # REPO-LEVEL CODE DEPTH
    
    def analyze_repo_depth(self, username: str, repo_name: str) -> Dict:
        """
        Analyze code depth for a specific repository.
        
        Checks:
        - Directory structure (src/, tests/, etc.)
        - README quality
        - CI/CD presence
        - File count and types
        """
        # Get repo contents
        contents = self._request(f"/repos/{username}/{repo_name}/contents")
        
        if not contents:
            return {"error": "Could not fetch repo contents"}
        
        # Analyze structure
        has_readme = False
        has_tests = False
        has_src = False
        has_ci = False
        has_docs = False
        has_config = False
        
        file_extensions = Counter()
        directories = []
        
        for item in contents:
            name = item.get("name", "").lower()
            item_type = item.get("type")
            
            if item_type == "dir":
                directories.append(name)
                if name in ["test", "tests", "__tests__", "spec"]:
                    has_tests = True
                elif name in ["src", "lib", "core", "app"]:
                    has_src = True
                elif name in ["docs", "documentation"]:
                    has_docs = True
                    
            elif item_type == "file":
                if name.startswith("readme"):
                    has_readme = True
                elif name in [".travis.yml", ".github", "jenkinsfile", ".circleci"]:
                    has_ci = True
                elif name in ["package.json", "requirements.txt", "cargo.toml", "go.mod", "pom.xml"]:
                    has_config = True
                
                # Count extensions
                if "." in name:
                    ext = name.rsplit(".", 1)[-1]
                    file_extensions[ext] += 1
        
        # Check for .github/workflows (CI/CD)
        github_contents = self._request(f"/repos/{username}/{repo_name}/contents/.github/workflows")
        if github_contents:
            has_ci = True
        
        # Get README content length
        readme_length = 0
        for item in contents:
            if item.get("name", "").lower().startswith("readme"):
                readme_data = self._request(f"/repos/{username}/{repo_name}/readme")
                if readme_data and readme_data.get("size"):
                    readme_length = readme_data.get("size", 0)
                break
        
        # Get commit count for this repo
        commits = self._request(f"/repos/{username}/{repo_name}/commits", params={"per_page": 1})
        commit_count = 0
        if commits:
            # Check link header for total count
            commit_count = len(commits)  # Simplified
        
        # Get contributors
        contributors = self._request(f"/repos/{username}/{repo_name}/contributors")
        contributor_count = len(contributors) if contributors else 0
        is_primary_contributor = False
        
        if contributors:
            for contrib in contributors:
                if contrib.get("login", "").lower() == username.lower():
                    # Check if > 50% of contributions
                    if contrib.get("contributions", 0) > sum(c.get("contributions", 0) for c in contributors) * 0.5:
                        is_primary_contributor = True
                    break
        
        # Calculate depth score
        depth_score = 0
        if has_readme: depth_score += 15
        if readme_length > 500: depth_score += 10
        if has_src: depth_score += 15
        if has_tests: depth_score += 20
        if has_ci: depth_score += 15
        if has_docs: depth_score += 10
        if has_config: depth_score += 10
        if is_primary_contributor: depth_score += 20
        
        return {
            "repo_name": repo_name,
            
            # Structure
            "has_readme": has_readme,
            "readme_length": readme_length,
            "has_tests": has_tests,
            "has_src_folder": has_src,
            "has_ci_cd": has_ci,
            "has_docs": has_docs,
            "has_config_files": has_config,
            
            # Contents
            "directories": directories,
            "file_types": dict(file_extensions.most_common(10)),
            
            # Ownership
            "contributor_count": contributor_count,
            "is_primary_contributor": is_primary_contributor,
            
            # Score
            "depth_score": depth_score,
            "depth_grade": "A" if depth_score >= 80 else ("B" if depth_score >= 60 else ("C" if depth_score >= 40 else "D"))
        }
    
    
    # BEST REPO SELECTION (ROLE-AGNOSTIC)
    
    def select_best_repositories(self, username: str, repos: List[Dict] = None, top_n: int = 5) -> Dict:
        """
        Select the BEST repositories that represent true engineering skill.
        
        Pure profile-based selection - NO job matching, NO bias.
        Answers: "What is the BEST engineering work on this GitHub?"
        
        Args:
            username: GitHub username
            repos: Pre-fetched repos (optional)
            top_n: Number of top repos to return
            
        Returns:
            Best repositories with scores and explanations
        """
        logger.info(f"Selecting best repositories for: {username}")
        
        if repos is None:
            repos = self.get_user_repos(username, max_repos=50)
        
        if not repos:
            return {"error": "No repositories found", "best_repositories": []}
        
        # STEP 1: Filter noise
        candidate_repos = self._filter_noise(repos)
        logger.info(f"After noise filter: {len(candidate_repos)}/{len(repos)} repos remain")
        
        if not candidate_repos:
            return {
                "error": "All repos filtered out as noise",
                "best_repositories": [],
                "filtered_count": len(repos)
            }
        
        # STEP 2-6: Score each repo
        scored_repos = []
        
        for repo in candidate_repos:
            repo_analysis = self._analyze_repo_for_selection(username, repo)
            scored_repos.append(repo_analysis)
        
        # Sort by composite score
        scored_repos.sort(key=lambda x: x.get("best_repo_score", 0), reverse=True)
        
        # Take top N
        best_repos = scored_repos[:top_n]
        
        return {
            "username": username,
            "total_repos": len(repos),
            "candidates_after_filter": len(candidate_repos),
            "best_repositories": best_repos,
            "selection_criteria": {
                "ownership_weight": 0.30,
                "engineering_depth_weight": 0.30,
                "development_maturity_weight": 0.20,
                "documentation_weight": 0.20
            }
        }
    
    
    def _filter_noise(self, repos: List[Dict]) -> List[Dict]:
        """
        STEP 1: Remove repos that cannot be evidence.
        
        Rejects:
        - Forks (unless heavily modified - TODO)
        - Tiny repos (< 20KB)
        - Very few commits
        - Empty / notes-only repos
        """
        CODE_EXTENSIONS = {
            "py", "js", "ts", "jsx", "tsx", "java", "go", "rs", "c", "cpp", 
            "h", "cs", "rb", "php", "swift", "kt", "scala", "vue", "svelte"
        }
        
        filtered = []
        
        for repo in repos:
            # Skip forks
            if repo.get("is_fork"):
                continue
            
            # Skip tiny repos (< 20KB)
            if repo.get("size", 0) < 20:
                continue
            
            # Must have a language (means there's code)
            if not repo.get("language"):
                continue
            
            # Skip very old untouched repos (TODO: add pushed_at check)
            
            filtered.append(repo)
        
        return filtered
    
    
    def _analyze_repo_for_selection(self, username: str, repo: Dict) -> Dict:
        """
        Analyze a single repo for best-repo selection.
        
        Calculates:
        - Ownership score (30%)
        - Engineering depth (30%)
        - Development maturity (20%)
        - Documentation score (20%)
        """
        repo_name = repo.get("name", "Unknown")
        
        # Get detailed repo analysis
        depth_analysis = self.analyze_repo_depth(username, repo_name)
        
        # Get commit activity for this repo
        commit_analysis = self._get_repo_commit_maturity(username, repo_name)
        
        # STEP 2: Ownership Score (0-100) - REFINED with sub-components
        ownership_result = self._calculate_ownership_score_v2(depth_analysis, repo, commit_analysis)
        ownership_score = ownership_result["total"]
        
        # STEP 3: Engineering Depth (already have from depth_analysis)
        engineering_depth = depth_analysis.get("depth_score", 0) if "error" not in depth_analysis else 0
        
        # STEP 4: Development Maturity (0-100)
        maturity_score, maturity_label = self._calculate_maturity_score(commit_analysis)
        
        # STEP 5: Documentation Score (0-100)
        doc_score = self._calculate_documentation_score(depth_analysis)
        
        # STEP 6: Composite Score
        best_repo_score = (
            ownership_score * 0.30 +
            engineering_depth * 0.30 +
            maturity_score * 0.20 +
            doc_score * 0.20
        )
        
        # STEP 7: Categorize repo (Primary / Supporting / Exploratory)
        category = self._categorize_repo(best_repo_score, maturity_label, ownership_score)
        
        # STEP 8: Generate disclaimers
        disclaimers = self._generate_disclaimers(maturity_label, engineering_depth, best_repo_score)
        
        # Generate "why selected" reasons
        why_selected = self._generate_selection_reasons(
            ownership_score, engineering_depth, maturity_label, doc_score, depth_analysis
        )
        
        return {
            "repo_name": repo_name,
            "url": repo.get("url"),
            "language": repo.get("language"),
            "description": repo.get("description"),
            "best_repo_score": round(best_repo_score, 1),
            "category": category,  # NEW: Primary / Supporting / Exploratory
            
            "why_selected": why_selected,
            "disclaimers": disclaimers,  # NEW: Context notes
            
            "signals": {
                "ownership": ownership_score,
                "ownership_breakdown": ownership_result["breakdown"],  # NEW: Sub-components
                "engineering_depth": engineering_depth,
                "documentation": doc_score,
                "maturity": maturity_label,
                "maturity_score": maturity_score
            },
            
            "details": {
                "size_kb": repo.get("size", 0),
                "stars": repo.get("stars", 0),
                "contributor_count": depth_analysis.get("contributor_count", 1) if "error" not in depth_analysis else 1,
                "is_primary_contributor": depth_analysis.get("is_primary_contributor", False) if "error" not in depth_analysis else False,
                "has_tests": depth_analysis.get("has_tests", False) if "error" not in depth_analysis else False,
                "has_ci_cd": depth_analysis.get("has_ci_cd", False) if "error" not in depth_analysis else False,
                "commit_analysis": commit_analysis
            }
        }
    
    
    def _calculate_ownership_score_v2(self, depth_analysis: Dict, repo: Dict, commit_analysis: Dict) -> Dict:
        """
        STEP 2 (REFINED): Calculate ownership with sub-components.
        
        Prevents everything clustering at 100.
        
        Sub-components:
        - Authorship (solo vs shared): 0-35
        - Commit Dominance (% of commits): 0-35
        - Repo Originality (not fork, meaningful size): 0-30
        """
        breakdown = {"authorship": 0, "commit_dominance": 0, "originality": 0}
        
        if "error" in depth_analysis:
            # Fallback: neutral score
            breakdown["originality"] = 20 if not repo.get("is_fork") else 5
            return {"total": sum(breakdown.values()), "breakdown": breakdown}
        
        # 1. AUTHORSHIP (0-35)
        contributor_count = depth_analysis.get("contributor_count", 1)
        if contributor_count == 1:
            breakdown["authorship"] = 35  # Solo author
        elif contributor_count == 2:
            breakdown["authorship"] = 25 if depth_analysis.get("is_primary_contributor") else 15
        elif contributor_count <= 5:
            breakdown["authorship"] = 15 if depth_analysis.get("is_primary_contributor") else 8
        else:
            breakdown["authorship"] = 10 if depth_analysis.get("is_primary_contributor") else 3
        
        # 2. COMMIT DOMINANCE (0-35)
        commit_ratio = commit_analysis.get("commit_ratio", 0) if "error" not in commit_analysis else 0.5
        if commit_ratio >= 0.95:
            breakdown["commit_dominance"] = 35
        elif commit_ratio >= 0.8:
            breakdown["commit_dominance"] = 28
        elif commit_ratio >= 0.6:
            breakdown["commit_dominance"] = 20
        elif commit_ratio >= 0.4:
            breakdown["commit_dominance"] = 12
        else:
            breakdown["commit_dominance"] = 5
        
        # 3. ORIGINALITY (0-30)
        if not repo.get("is_fork"):
            breakdown["originality"] = 15
        else:
            breakdown["originality"] = 0
        
        # Size bonus
        size = repo.get("size", 0)
        if size > 500:
            breakdown["originality"] += 15
        elif size > 100:
            breakdown["originality"] += 10
        elif size > 50:
            breakdown["originality"] += 5
        
        total = min(100, sum(breakdown.values()))
        return {"total": total, "breakdown": breakdown}
    
    
    def _get_repo_commit_maturity(self, username: str, repo_name: str) -> Dict:
        """
        Get commit maturity signals for a single repo.
        """
        commits = self._request(
            f"/repos/{username}/{repo_name}/commits",
            params={"per_page": 100}
        )
        
        if not commits:
            return {"error": "No commits found", "total_commits": 0}
        
        commit_dates = []
        author_commits = 0
        
        for commit in commits:
            date_str = commit.get("commit", {}).get("author", {}).get("date")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    commit_dates.append(dt)
                except:
                    pass
            
            # Check if user is author
            author = commit.get("author", {})
            if author and author.get("login", "").lower() == username.lower():
                author_commits += 1
        
        if not commit_dates:
            return {"error": "Could not parse commits", "total_commits": len(commits)}
        
        commit_dates.sort()
        
        # Calculate time span
        first_commit = commit_dates[0]
        last_commit = commit_dates[-1]
        days_span = (last_commit - first_commit).days
        
        # Calculate unique commit days
        unique_days = len(set(d.date() for d in commit_dates))
        
        # Calculate commit ratio (user's commits / total)
        commit_ratio = author_commits / len(commits) if commits else 0
        
        return {
            "total_commits": len(commits),
            "author_commits": author_commits,
            "commit_ratio": round(commit_ratio, 2),
            "days_span": days_span,
            "unique_commit_days": unique_days,
            "first_commit": first_commit.isoformat(),
            "last_commit": last_commit.isoformat(),
            "is_iterative": days_span > 7 and unique_days > 3
        }
    
    
    def _calculate_maturity_score(self, commit_analysis: Dict) -> Tuple[int, str]:
        """
        STEP 4: Calculate development maturity score (0-100).
        
        Signals:
        - Time span (days between first/last commit)
        - Multiple commit days
        - Iterative development
        - Not just 1 massive commit
        """
        if "error" in commit_analysis:
            return 30, "unknown"
        
        score = 0
        
        days_span = commit_analysis.get("days_span", 0)
        unique_days = commit_analysis.get("unique_commit_days", 1)
        total_commits = commit_analysis.get("total_commits", 1)
        commit_ratio = commit_analysis.get("commit_ratio", 0)
        
        # Time span scoring
        if days_span >= 90:
            score += 30
            label = "long-term"
        elif days_span >= 30:
            score += 25
            label = "medium-term"
        elif days_span >= 7:
            score += 15
            label = "short-term"
        else:
            score += 5
            label = "quick-build"
        
        # Multiple commit days (iterative development)
        if unique_days >= 10:
            score += 30
        elif unique_days >= 5:
            score += 20
        elif unique_days >= 3:
            score += 10
        else:
            score += 0
        
        # Total commits
        if total_commits >= 50:
            score += 20
        elif total_commits >= 20:
            score += 15
        elif total_commits >= 10:
            score += 10
        elif total_commits >= 5:
            score += 5
        
        # Commit ratio (user's ownership of commits)
        if commit_ratio >= 0.9:
            score += 20
        elif commit_ratio >= 0.7:
            score += 15
        elif commit_ratio >= 0.5:
            score += 10
        
        # Determine final label
        if commit_analysis.get("is_iterative"):
            label = "iterative"
        elif unique_days <= 2:
            label = "one-shot"
        
        return min(100, score), label
    
    
    def _calculate_documentation_score(self, depth_analysis: Dict) -> int:
        """
        STEP 5: Calculate documentation score (0-100).
        
        Signals:
        - README exists
        - README length
        - Has docs folder
        - Has config files (setup intent)
        """
        if "error" in depth_analysis:
            return 20  # Unknown
        
        score = 0
        
        # README exists
        if depth_analysis.get("has_readme"):
            score += 30
        
        # README length
        readme_len = depth_analysis.get("readme_length", 0)
        if readme_len >= 2000:
            score += 30  # Comprehensive
        elif readme_len >= 1000:
            score += 25
        elif readme_len >= 500:
            score += 20
        elif readme_len >= 200:
            score += 10
        elif readme_len > 0:
            score += 5
        
        # Has docs folder
        if depth_analysis.get("has_docs"):
            score += 20
        
        # Has config files (shows setup intent)
        if depth_analysis.get("has_config_files"):
            score += 10
        
        # Has src folder (organized)
        if depth_analysis.get("has_src_folder"):
            score += 10
        
        return min(100, score)
    
    
    def _generate_selection_reasons(
        self, 
        ownership: int, 
        depth: int, 
        maturity: str, 
        doc: int,
        depth_analysis: Dict
    ) -> List[str]:
        """Generate human-readable reasons for why this repo was selected."""
        reasons = []
        
        # Ownership reasons
        if ownership >= 90:
            reasons.append("Single-author project with full ownership")
        elif ownership >= 70:
            reasons.append("Primary contributor with strong ownership")
        elif ownership >= 50:
            reasons.append("Meaningful contribution to project")
        
        # Depth reasons
        if "error" not in depth_analysis:
            if depth_analysis.get("has_tests"):
                reasons.append("Has test suite (engineering discipline)")
            if depth_analysis.get("has_ci_cd"):
                reasons.append("CI/CD pipeline configured")
            if depth_analysis.get("has_src_folder"):
                reasons.append("Organized folder structure")
            if depth_analysis.get("contributor_count", 0) == 1:
                reasons.append("Solo-built project")
            if len(depth_analysis.get("directories", [])) >= 3:
                reasons.append("Multi-module architecture")
        
        # Maturity reasons
        if maturity == "iterative":
            reasons.append("Consistent development over time")
        elif maturity == "long-term":
            reasons.append("Long-term project (90+ days)")
        elif maturity == "medium-term":
            reasons.append("Sustained development effort")
        
        # Documentation reasons
        if doc >= 70:
            reasons.append("Well-documented with clear intent")
        elif doc >= 40:
            reasons.append("Has project documentation")
        
        # Cap at 5 reasons
        return reasons[:5] if reasons else ["Passed basic engineering criteria"]
    
    
    def _categorize_repo(self, score: float, maturity: str, ownership: int) -> str:
        """
        Categorize repo as Primary Evidence / Supporting Evidence / Exploratory.
        
        This prevents low-scoring repos from being called "BEST".
        """
        # Primary Evidence: High score + good maturity + strong ownership
        if score >= 60 and ownership >= 50:
            return "Primary Evidence"
        
        # Supporting Evidence: Moderate score, shows learning or collaboration
        elif score >= 40 or (maturity == "iterative" and score >= 30):
            return "Supporting Evidence"
        
        # Exploratory: Low score, experiments, one-shots
        else:
            return "Exploratory / Learning"
    
    
    def _generate_disclaimers(self, maturity: str, depth: int, score: float) -> List[str]:
        """
        Generate context notes / disclaimers for transparency.
        
        E.g., "High structural clarity, limited lifecycle evidence"
        """
        disclaimers = []
        
        # One-shot disclaimer
        if maturity == "one-shot":
            if depth >= 60:
                disclaimers.append("High structural clarity, limited lifecycle evidence")
            else:
                disclaimers.append("Single-session build, may be hackathon or experiment")
        
        # Quick-build disclaimer
        if maturity == "quick-build":
            disclaimers.append("Rapid development, minimal iteration history")
        
        # Low ownership but analyzed
        if score < 40:
            disclaimers.append("Lower score - may be learning project or contribution")
        
        # High depth but no tests
        if depth >= 50 and depth < 70:
            disclaimers.append("Good structure, but no test suite detected")
        
        return disclaimers
    
    
    # MASTER PROFILE ANALYSIS


    
    def analyze_full_profile(self, username: str) -> Dict:
        """
        Complete GitHub profile analysis.
        
        Returns:
            - credibility_signal
            - skill_signal
            - consistency_signal
        """
        logger.info(f"Analyzing GitHub profile: {username}")
        
        # 1. User profile
        user = self.get_user_profile(username)
        if not user:
            return {"error": f"User not found: {username}"}
        
        credibility = self.calculate_credibility_score(user)
        
        # 2. Repos and languages
        repos = self.get_user_repos(username)
        languages = self.aggregate_languages(username, repos)
        
        # 3. Commit activity
        commit_activity = self.get_commit_activity(username, repos)
        
        # 5. Best Repositories Selection (NEW - Role-Agnostic)
        best_repos_result = self.select_best_repositories(username, repos, top_n=5)
        best_repos = best_repos_result.get("best_repositories", [])
        
        # Calculate aggregate signals
        avg_depth = sum(r.get("signals", {}).get("engineering_depth", 0) for r in best_repos) / len(best_repos) if best_repos else 0
        
        # Consistency score
        consistency_score = 0
        if commit_activity.get("active_weeks_ratio", 0) >= 0.5:
            consistency_score += 40
        elif commit_activity.get("active_weeks_ratio", 0) >= 0.3:
            consistency_score += 25
        if commit_activity.get("commits_last_30_days", 0) >= 10:
            consistency_score += 30
        elif commit_activity.get("commits_last_30_days", 0) >= 5:
            consistency_score += 20
        if commit_activity.get("max_gap_days", 999) < 30:
            consistency_score += 30
        elif commit_activity.get("max_gap_days", 999) < 60:
            consistency_score += 15
        
        return {
            "username": username,
            "analyzed_at": datetime.now().isoformat(),
            
            # User profile
            "profile": user,
            
            # Three main signals
            "credibility_signal": {
                "score": credibility["credibility_score"],
                "flags": credibility["flags"],
                "account_age_years": user["account_age_years"],
                "is_verified": credibility["credibility_score"] >= 50 and not credibility["flags"]
            },
            
            "skill_signal": {
                "primary_language": languages.get("primary_language"),
                "verified_languages": languages.get("verified_languages", []),
                "language_distribution": languages.get("languages_by_bytes", {}),
                "original_repos": languages.get("original_repos_analyzed", 0),
                "avg_code_depth": round(avg_depth, 1),
                "best_repositories": best_repos,  # NEW: Role-agnostic best repos
                "detected_frameworks": self._scan_top_repos_for_frameworks(username, best_repos[:3]) # NEW: Deep Code Scan
            },
            
            "consistency_signal": {
                "score": consistency_score,
                "commits_last_30_days": commit_activity.get("commits_last_30_days", 0),
                "commits_last_year": commit_activity.get("commits_last_year", 0),
                "active_weeks_ratio": commit_activity.get("active_weeks_ratio", 0),
                "max_gap_days": commit_activity.get("max_gap_days", 0),
                "patterns": commit_activity.get("patterns", []),
                "days_since_last_commit": commit_activity.get("days_since_last_commit")
            },
            
            # Summary
            "summary": {
                "credibility_verified": credibility["credibility_score"] >= 50,
                "primary_skill": languages.get("primary_language"),
                "is_consistent": consistency_score >= 50,
                "is_active": commit_activity.get("days_since_last_commit", 999) < 30,
                "red_flags": credibility["flags"] + commit_activity.get("patterns", [])
            },
            
            # Raw data for debugging
            "raw": {
                "repos": repos,
                "commit_activity": commit_activity
            }
        }

    def _scan_top_repos_for_frameworks(self, username: str, best_repos: List[Dict]) -> List[str]:
        """
        Scan top repositories for actual framework usage (Deep Scan).
        """
        detected_frameworks = set()
        
        for repo in best_repos:
            repo_name = repo.get("repo_name", repo.get("name"))
            if not repo_name: continue
            
            full_name = f"{username}/{repo_name}"
            language = repo.get("language")
            
            if not language: continue
            
            logger.info(f"Deep scanning {full_name} ({language}) for frameworks...")
            
            try:
                # Use existing scan_repo_for_frameworks method
                scan_result = self.scan_repo_for_frameworks(full_name, language)
                detections = scan_result.get("detections", [])
                
                for d in detections:
                    # Include detected framework skills across all confidence tiers
                    detected_frameworks.add(d["skill"])
                    logger.info(f"Detected {d['skill']} in {repo_name}")
            except Exception as e:
                logger.error(f"Failed to scan {full_name}: {e}")
                
        return list(detected_frameworks)

    
    
    def generate_skill_narrative(self, analysis: Dict) -> Dict:
        """
        Generate human-readable skill narrative and verification recommendations.
        
        This is what judges love - transparent, explainable, honest evaluation.
        
        Args:
            analysis: Full profile analysis from analyze_full_profile()
            
        Returns:
            Narrative summary with verification status and recommendations
        """
        if "error" in analysis:
            return {"error": analysis["error"]}
        
        profile = analysis.get("profile", {})
        cred = analysis.get("credibility_signal", {})
        skill = analysis.get("skill_signal", {})
        consistency = analysis.get("consistency_signal", {})
        summary = analysis.get("summary", {})
        
        # 1. CREDIBILITY EVALUATION
        cred_status = "PASS" if cred.get("is_verified") else "REVIEW"
        cred_details = []
        
        age = profile.get("account_age_years", 0)
        if age >= 3:
            cred_details.append(f"Account age: {age} years → established developer")
        elif age >= 1:
            cred_details.append(f"Account age: {age} years → acceptable for early-career")
        else:
            cred_details.append(f"Account age: {age} years → new account, requires verification")
        
        if profile.get("has_bio"):
            cred_details.append("Real bio present")
        if profile.get("has_company"):
            cred_details.append(f"Company: {profile.get('company')}")
        if profile.get("email"):
            cred_details.append("Email publicly visible (rare, strong signal)")
        if profile.get("followers", 0) > 10:
            cred_details.append(f"Followers: {profile.get('followers')} → community presence")
        
        # 2. SKILL EVALUATION
        primary = skill.get("primary_language")
        verified_langs = skill.get("verified_languages", [])
        
        skill_narrative = []
        if primary:
            skill_narrative.append(f"Primary skill: {primary}")
        if verified_langs:
            skill_narrative.append(f"Verified languages: {', '.join(verified_langs)}")
        
        # Domain detection from repo names/descriptions
        repos = analysis.get("raw", {}).get("repos", [])
        domains = self._detect_domains(repos)
        if domains:
            skill_narrative.append(f"Domain expertise signals: {', '.join(domains)}")
        
        # 3. PROJECT DEPTH EVALUATION
        repo_depths = skill.get("top_repo_depths", [])
        depth_summary = []
        
        for rd in repo_depths:
            if "error" in rd:
                continue
            name = rd.get("repo_name", "Unknown")
            grade = rd.get("depth_grade", "?")
            owner = "Primary contributor" if rd.get("is_primary_contributor") else "Contributor"
            depth_summary.append(f"{name}: Grade {grade}, {owner}")
        
        avg_depth = skill.get("avg_code_depth", 0)
        
        # 4. CONSISTENCY INTERPRETATION
        cons_score = consistency.get("score", 0)
        patterns = consistency.get("patterns", [])
        commits_30 = consistency.get("commits_last_30_days", 0)
        last_commit_days = consistency.get("days_since_last_commit")
        
        consistency_narrative = []
        if "consistent_contributor" in patterns:
            consistency_narrative.append("Consistent contributor (regular activity)")
        if "long_inactivity_gaps" in patterns:
            consistency_narrative.append("Project-based contributor (hackathons/sprints pattern)")
        if "burst_activity" in patterns:
            consistency_narrative.append("Burst-only activity (may indicate deadline-driven work)")
        if "weekend_only" in patterns:
            consistency_narrative.append("Weekend-only commits (may be side projects)")
        
        if commits_30 > 0:
            consistency_narrative.append(f"Currently active: {commits_30} commits in last 30 days")
        
        if last_commit_days is not None:
            if last_commit_days <= 7:
                consistency_narrative.append("Very recent activity (last week)")
            elif last_commit_days <= 30:
                consistency_narrative.append(f"Recent activity ({last_commit_days} days ago)")
        
        # 5. RED FLAG ANALYSIS
        red_flags = summary.get("red_flags", [])
        flag_analysis = []
        
        for flag in red_flags:
            if flag == "long_inactivity_gaps":
                flag_analysis.append({
                    "flag": flag,
                    "severity": "low",
                    "interpretation": "Gaps are normal for milestone-driven work",
                    "action": "Add context note, not penalty"
                })
            elif flag == "new_account_under_6_months":
                flag_analysis.append({
                    "flag": flag,
                    "severity": "medium",
                    "interpretation": "New account requires verification",
                    "action": "Cross-check with other platforms"
                })
            elif flag == "burst_activity":
                flag_analysis.append({
                    "flag": flag,
                    "severity": "low",
                    "interpretation": "May indicate hackathon or exam-driven work",
                    "action": "Context note only"
                })
            else:
                flag_analysis.append({
                    "flag": flag,
                    "severity": "medium",
                    "interpretation": "Requires review",
                    "action": "Manual verification recommended"
                })
        
        # 6. GENERATE FINAL NARRATIVE
        # This is what beats ATS - a human-readable summary
        experience_level = self._infer_experience_level(profile, repos, consistency)
        
        narrative = f"{experience_level} with "
        
        if verified_langs:
            narrative += f"verified {' and '.join(verified_langs[:2])} skills, "
        
        if domains:
            narrative += f"hands-on experience in {', '.join(domains[:2])}"
        else:
            narrative += "hands-on project experience"
        
        narrative += ". "
        
        if "consistent_contributor" in patterns:
            narrative += "Demonstrates consistent contribution patterns. "
        elif commits_30 > 0:
            narrative += "Shows recent activity and engagement. "
        
        if "long_inactivity_gaps" in patterns:
            narrative += "Some inconsistency in long-term patterns, typical of hackathon or milestone-driven work. "
        
        # 7. VERIFICATION RECOMMENDATION
        verification_status = "PROVISIONAL"
        recommendations = []
        
        # Determine verification strength
        if cred.get("is_verified") and cons_score >= 50 and avg_depth >= 50:
            verification_status = "STRONG"
            recommendations.append("Issue full skill verification")
            recommendations.append("Skip basic skill test")
        elif cred.get("is_verified") and (cons_score >= 30 or commits_30 > 0):
            verification_status = "PROVISIONAL"
            recommendations.append("Issue provisional skill verification")
            recommendations.append("Short skill test OR interview recommended")
            recommendations.append("Cross-check with LeetCode/resume")
        else:
            verification_status = "REQUIRES_VERIFICATION"
            recommendations.append("Skill test required")
            recommendations.append("Cross-verify with other platforms")
        
        return {
            "narrative": narrative.strip(),
            "verification_status": verification_status,
            
            "evaluation": {
                "credibility": {
                    "status": cred_status,
                    "details": cred_details
                },
                "skills": {
                    "primary": primary,
                    "verified": verified_langs,
                    "domains": domains,
                    "narrative": skill_narrative
                },
                "project_depth": {
                    "avg_score": avg_depth,
                    "repos": depth_summary
                },
                "consistency": {
                    "score": cons_score,
                    "narrative": consistency_narrative
                }
            },
            
            "red_flags": flag_analysis,
            "recommendations": recommendations,
            
            "judge_friendly_summary": {
                "one_liner": narrative.strip(),
                "evidence_backed": len(verified_langs) > 0,
                "active_recently": commits_30 > 0 or (last_commit_days is not None and last_commit_days < 30),
                "concerns": [f["flag"] for f in flag_analysis if f["severity"] != "low"]
            }
        }
    
    
    def _detect_domains(self, repos: List[Dict]) -> List[str]:
        """Detect domain expertise from repo names, descriptions, and topics"""
        domain_keywords = {
            "web": ["web", "frontend", "backend", "react", "vue", "angular", "node", "express"],
            "uav/robotics": ["uav", "drone", "px4", "mavlink", "robot", "ros", "autonomy"],
            "machine learning": ["ml", "ai", "deep", "neural", "model", "yolo", "detection", "cv"],
            "mobile": ["android", "ios", "flutter", "react-native", "mobile", "app"],
            "devops": ["docker", "kubernetes", "ci", "cd", "deploy", "infra", "terraform"],
            "data": ["data", "analytics", "etl", "pipeline", "sql", "database"],
            "blockchain": ["blockchain", "web3", "solidity", "ethereum", "crypto"]
        }
        
        detected = set()
        
        for repo in repos:
            name = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
            topics = repo.get("topics", [])
            
            for domain, keywords in domain_keywords.items():
                if any(kw in name for kw in keywords):
                    detected.add(domain)
                if any(kw in " ".join(topics) for kw in keywords):
                    detected.add(domain)
        
        return list(detected)
    
    
    def _infer_experience_level(self, profile: Dict, repos: List[Dict], consistency: Dict) -> str:
        """Infer experience level from signals"""
        age = profile.get("account_age_years", 0)
        repo_count = len([r for r in repos if not r.get("is_fork")])
        commits_year = consistency.get("commits_last_year", 0)
        
        if age >= 5 and repo_count >= 20 and commits_year >= 200:
            return "Senior engineer"
        elif age >= 3 and repo_count >= 10:
            return "Mid-level engineer"
        elif age >= 1 and repo_count >= 5:
            return "Early-career engineer"
        else:
            return "Junior developer"


# Convenience function
def analyze_github_profile(username: str, token: str = None) -> Dict:
    """Quick function to analyze a GitHub profile"""
    client = GitHubAPIClient(token=token)
    return client.analyze_full_profile(username)


def analyze_github_with_narrative(username: str, token: str = None) -> Dict:
    """Analyze GitHub profile and generate skill narrative"""
    client = GitHubAPIClient(token=token)
    analysis = client.analyze_full_profile(username)
    narrative = client.generate_skill_narrative(analysis)
    return {
        "analysis": analysis,
        "narrative": narrative
    }



if __name__ == "__main__":
    import sys
    import argparse
    import os
    import json # Added for json.dumps
    
    # Add parent directory to path for config import
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    parser = argparse.ArgumentParser(description="Analyze GitHub profile")
    parser.add_argument("username", help="GitHub username to analyze")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON without formatting")
    parser.add_argument("--save", action="store_true", help="Save output to github_output.json")
    args = parser.parse_args()
    
    username = args.username
    json_only = args.json_only
    save = args.save
    
    # Try to load token from config first, then env
    token = os.getenv("GITHUB_PAT")
    try:
        from config import GITHUB_PAT
        token = GITHUB_PAT
        print(f"✅ Loaded GitHub PAT from config.py")
    except ImportError:
        print("⚠️ Could not import from config.py, using env variable")
    
    client = GitHubAPIClient(token=token)
    result = client.analyze_full_profile(username)
    
    # Save to file if requested
    if save:
        output_file = "github_output.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        if not json_only:
            print(f"\n💾 Saved to: {output_file}")
    
    # Output based on json_only flag
    if json_only:
        # Clean JSON output only (no emojis, no formatting)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Formatted narrative output
        narrative = client.generate_skill_narrative(result)
        
        print("\n" + "=" * 60)
        print("� SKILL NARRATIVE (Judge-Friendly)")
        print("=" * 60)
        print(f"\n🎯 {narrative.get('narrative', 'N/A')}\n")
        print(f"📊 Verification Status: {narrative.get('verification_status', 'N/A')}")
        
        print("\n�📌 Recommendations:")
        for rec in narrative.get("recommendations", []):
            print(f"   → {rec}")
        
        if narrative.get("red_flags"):
            print("\n⚠️ Red Flags:")
            for flag in narrative.get("red_flags", []):
                print(f"   • {flag['flag']} ({flag['severity']}): {flag['interpretation']}")
        
        # Show best repositories grouped by category
        best_repos = result.get("skill_signal", {}).get("best_repositories", [])
        if best_repos:
            print("\n" + "=" * 60)
            print("🏆 REPOSITORY ANALYSIS (Role-Agnostic Selection)")
            print("=" * 60)
            
            # Group by category
            categories = {"Primary Evidence": [], "Supporting Evidence": [], "Exploratory / Learning": []}
            for repo in best_repos:
                cat = repo.get("category", "Exploratory / Learning")
                categories[cat].append(repo)
            
            # Display each category
            for cat_name, repos in categories.items():
                if repos:
                    icon = "🟢" if cat_name == "Primary Evidence" else ("🟡" if cat_name == "Supporting Evidence" else "⚪")
                    print(f"\n{icon} {cat_name.upper()}")
                    print("-" * 40)
                    
                    for repo in repos:
                        score = repo.get("best_repo_score", 0)
                        name = repo.get("repo_name", "Unknown")
                        lang = repo.get("language", "Unknown")
                        
                        print(f"\n  📁 {name} [{lang}] — Score: {score}/100")
                        
                        # Show signals with breakdown
                        signals = repo.get("signals", {})
                        breakdown = signals.get("ownership_breakdown", {})
                        print(f"     📊 Ownership: {signals.get('ownership', 0)} (auth:{breakdown.get('authorship', 0)} + dom:{breakdown.get('commit_dominance', 0)} + orig:{breakdown.get('originality', 0)})")
                        print(f"     📊 Depth: {signals.get('engineering_depth', 0)} | Docs: {signals.get('documentation', 0)} | Maturity: {signals.get('maturity', 'N/A')}")
                        
                        # Show why selected
                        why = repo.get("why_selected", [])
                        if why:
                            print(f"     ✓ {' • '.join(why[:3])}")
                        
                        # Show disclaimers
                        disclaimers = repo.get("disclaimers", [])
                        if disclaimers:
                            print(f"     ⚠️ {disclaimers[0]}")
    
    # Option to show full JSON
    if "--json" in sys.argv:
        print("\n" + "=" * 60)
        print("📦 RAW ANALYSIS")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
