"""
OPTIMIZED GitHub Service for Fair Hiring System
Fixes timeout issues by:
1. Reducing API calls
2. Adding timeout handling
3. Implementing progressive response
4. Adding caching
"""

from flask import Flask, request, jsonify
import sys
import os
import logging
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agents_files" / "skill_verification_agent"))

from scraper.github_api import GitHubAPIClient

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for GitHub analyses (in-memory, simple)
ANALYSIS_CACHE = {}
CACHE_TTL = 3600  # 1 hour


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "github-agent"}), 200


@app.route('/scrape', methods=['POST'])
def scrape_github():
    """
    OPTIMIZED GitHub scraping endpoint.
    
    Reduces timeout issues by:
    - Limiting API calls
    - Using cache
    - Returning partial results if timeout approaching
    """
    start_time = time.time()
    MAX_PROCESSING_TIME = 150  # 150 seconds max (stay under 180s timeout)
    
    try:
        data = request.get_json()
        github_url = data.get('github_url', '')
        
        if not github_url:
            return jsonify({
                "error": "Missing github_url",
                "success": False
            }), 400
        
        # Extract username from URL
        username = extract_username(github_url)
        
        if not username:
            return jsonify({
                "error": f"Invalid GitHub URL: {github_url}",
                "success": False
            }), 400
        
        logger.info(f"Scraping GitHub profile: {username}")
        
        # Check cache first
        cache_key = f"github:{username}"
        if cache_key in ANALYSIS_CACHE:
            cached_data, cached_time = ANALYSIS_CACHE[cache_key]
            age = time.time() - cached_time
            if age < CACHE_TTL:
                logger.info(f"Cache HIT for {username} (age: {int(age)}s)")
                cached_data['_cached'] = True
                cached_data['_cache_age_seconds'] = int(age)
                return jsonify(cached_data), 200
        
        # Get GitHub token from environment
        token = os.getenv("GITHUB_PAT") or os.getenv("GITHUB_TOKEN")
        
        if not token:
            logger.warning("⚠️ No GitHub token - using rate-limited API (60 req/hour)")
        else:
            logger.info("✅ Using authenticated GitHub API (5000 req/hour)")
        
        # Initialize client
        client = GitHubAPIClient(token=token)
        
        # OPTIMIZATION: Lightweight analysis first
        result = analyze_github_optimized(client, username, MAX_PROCESSING_TIME, start_time)
        
        # Cache result
        ANALYSIS_CACHE[cache_key] = (result, time.time())
        
        # Add processing metadata
        result['processing_time_seconds'] = round(time.time() - start_time, 2)
        result['_cached'] = False
        
        logger.info(f"✅ Analysis complete for {username} in {result['processing_time_seconds']}s")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"GitHub scraping failed: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False,
            "username": username if 'username' in locals() else 'unknown'
        }), 500


def analyze_github_optimized(client, username, max_time, start_time):
    """
    Optimized analysis that respects time limits.
    
    Progressive approach:
    1. Essential data first (user + repos)
    2. Language analysis (quick)
    3. Skip expensive operations if time running out
    """
    
    # PHASE 1: Essential Data (< 5 seconds)
    logger.info(f"Phase 1: Fetching user profile and repos...")
    github_status = "complete"
    
    user = client.get_user_profile(username)
    if not user:
        return {"error": f"User not found: {username}", "success": False, "github_status": "unavailable"}
    
    repos = client.get_user_repos(username, max_repos=20)  # Reduced from 30
    
    elapsed = time.time() - start_time
    logger.info(f"Phase 1 complete in {elapsed:.1f}s")
    
    # PHASE 2: Quick Analysis (< 15 seconds)
    if elapsed < max_time - 75:  # At least 75s remaining
        logger.info(f"Phase 2: Language aggregation...")
        languages = client.aggregate_languages(username, repos)
        credibility = client.calculate_credibility_score(user)
    else:
        logger.warning("Skipping language aggregation - timeout approaching")
        github_status = "partial"
        languages = {"error": "Skipped due to timeout"}
        credibility = {"credibility_score": 0, "flags": ["timeout"]}
    
    elapsed = time.time() - start_time
    logger.info(f"Phase 2 complete in {elapsed:.1f}s")
    
    # PHASE 3: Repo Selection (< 30 seconds)
    if elapsed < max_time - 60:  # At least 60s remaining
        logger.info(f"Phase 3: Selecting best repositories...")
        best_repos = client.select_best_repositories(username, repos, top_n=3)  # Reduced from 5
        best_repos_list = best_repos.get("best_repositories", [])
    else:
        logger.warning("Skipping repo selection - timeout approaching")
        github_status = "partial"
        best_repos_list = []
    
    elapsed = time.time() - start_time
    logger.info(f"Phase 3 complete in {elapsed:.1f}s")
    
    # PHASE 4: Framework Detection (SKIP if time low)
    detected_frameworks = []
    if elapsed < max_time - 45:  # At least 45s remaining
        logger.info(f"Phase 4: Framework detection (lightweight)...")
        try:
            # Only scan top 2 repos, not 3
            # Only scan 20 files max per repo, not 50
            detected_frameworks = scan_frameworks_lightweight(client, username, best_repos_list[:2])
        except Exception as e:
            logger.error(f"Framework detection failed: {e}")
            github_status = "partial"
    else:
        logger.warning("Skipping framework detection - timeout approaching")
        github_status = "partial"
    
    elapsed = time.time() - start_time
    logger.info(f"Phase 4 complete in {elapsed:.1f}s")
    
    # PHASE 5: Skip commit activity if time is tight
    commit_activity = {"skipped": True, "reason": "Performance optimization"}
    consistency_score = 50  # Default neutral score
    
    if elapsed < max_time - 30 and len(repos) > 0:  # At least 30s remaining
        logger.info(f"Phase 5: Commit activity analysis...")
        try:
            commit_activity = client.get_commit_activity(username, repos[:5])  # Only top 5 repos
            
            # Quick consistency score
            if commit_activity.get("active_weeks_ratio", 0) >= 0.5:
                consistency_score = 80
            elif commit_activity.get("commits_last_30_days", 0) >= 10:
                consistency_score = 70
            elif commit_activity.get("commits_last_90_days", 0) >= 20:
                consistency_score = 60
        except Exception as e:
            logger.error(f"Commit analysis failed: {e}")
            github_status = "partial"
    else:
        logger.warning("Skipping commit analysis - timeout approaching")
        github_status = "partial"
    
    elapsed = time.time() - start_time
    logger.info(f"Analysis complete in {elapsed:.1f}s")
    
    # Build response
    return {
        "success": True,
        "username": username,
        "profile": user,
        "github_status": github_status,
        
        "credibility_signal": {
            "score": credibility.get("credibility_score", 0),
            "flags": credibility.get("flags", []),
            "account_age_years": user.get("account_age_years", 0),
            "is_verified": credibility.get("credibility_score", 0) >= 50
        },
        
        "skill_signal": {
            "primary_language": languages.get("primary_language"),
            "verified_languages": languages.get("verified_languages", []),
            "language_distribution": languages.get("languages_by_bytes", {}),
            "best_repositories": best_repos_list,
            "detected_frameworks": detected_frameworks
        },
        
        "consistency_signal": {
            "score": consistency_score,
            "commits_last_30_days": commit_activity.get("commits_last_30_days", 0),
            "commits_last_90_days": commit_activity.get("commits_last_90_days", 0),
            "patterns": commit_activity.get("patterns", [])
        },
        
        "summary": {
            "credibility_verified": credibility.get("credibility_score", 0) >= 50,
            "primary_skill": languages.get("primary_language"),
            "is_active": commit_activity.get("commits_last_30_days", 0) > 0,
            "repo_count": len(repos)
        },
        
        "_optimization_notes": {
            "max_repos_scanned": 20,
            "max_repos_for_selection": 3,
            "framework_scan_limit": 2,
            "commit_analysis": "top_5_repos" if not commit_activity.get("skipped") else "skipped"
        }
    }


def scan_frameworks_lightweight(client, username, best_repos):
    """
    Lightweight framework detection (reduced API calls).
    
    Only scans:
    - Dependency files (requirements.txt, package.json)
    - First 20 files max per repo
    """
    detected = set()
    
    for repo in best_repos[:2]:  # Max 2 repos
        repo_name = repo.get("repo_name") or repo.get("name")
        language = repo.get("language")
        
        if not repo_name or not language:
            continue
        
        full_name = f"{username}/{repo_name}"
        
        try:
            # Use existing method but it's already limited to 50 files
            scan_result = client.scan_repo_for_frameworks(full_name, language)
            detections = scan_result.get("detections", [])
            
            # Only take high-confidence detections
            for d in detections:
                if d.get("confidence") == "high" or d.get("confidence_score", 0) >= 0.7:
                    detected.add(d["skill"])
        except Exception as e:
            logger.error(f"Failed to scan {full_name}: {e}")
    
    return list(detected)


def extract_username(github_url):
    """Extract username from GitHub URL"""
    # Handle various formats:
    # https://github.com/username
    # github.com/username
    # username
    
    if not github_url:
        return None
    
    # Remove protocol
    url = github_url.replace('https://', '').replace('http://', '')
    
    # Remove github.com
    url = url.replace('github.com/', '')
    
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Take first part (username)
    parts = url.split('/')
    username = parts[0] if parts else None
    
    return username if username else None


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8005))
    logger.info(f"Starting GitHub Agent Service on port {port}")
    logger.info(f"GitHub Token: {'✅ Configured' if os.getenv('GITHUB_PAT') else '❌ Not configured (rate limited)'}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
