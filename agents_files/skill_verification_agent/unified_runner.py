"""
Unified Runner for Complete Skill Verification Pipeline

Orchestrates all 5 evidence sources:
1. ATS Resume (PDF)
2. LinkedIn (PDF) 
3. GitHub (API)
4. LeetCode (scraper)
5. Codeforces (scraper)

Then feeds into:
- Evidence Graph Builder
- Skill Verification Agent V2

Output: Complete credential with all signals
"""
import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.ats import process_resume_pdf
from scraper.linkedin_parser import LinkedInPDFParser
from scraper.github_api import GitHubAPIClient
from scraper.leetcode_tool import analyze_leetcode_profile
from scraper.codeforce_tool import analyze_codeforces_profile
from agents.evidence_graph_builder import EvidenceGraphBuilder
from agents.skill_verification_agent_v2 import SkillVerificationAgent
from config import GITHUB_PAT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_complete_verification(
    resume_pdf: str = None,
    linkedin_pdf: str = None,
    github_username: str = None,
    leetcode_url: str = None,
    codeforces_url: str = None,
    output_file: str = "final_result.json"
):
    """
    Run complete skill verification with all 5 sources.
    
    Args:
        resume_pdf: Path to resume PDF
        linkedin_pdf: Path to LinkedIn PDF
        github_username: GitHub username
        leetcode_url: LeetCode profile URL
        codeforces_url: Codeforces profile URL
        output_file: Output JSON file path
    
    Returns:
        Complete credential JSON
    """
    print("="*60)
    print("🚀 SKILL VERIFICATION PIPELINE - ALL SOURCES")
    print("="*60)
    
    evidence_files = {}
    
    # STEP 1: ATS Resume Processing
    if resume_pdf and os.path.exists(resume_pdf):
        print(f"\n📄 Processing Resume: {resume_pdf}")
        ats_output = process_resume_pdf(resume_pdf)
        evidence_files['ats'] = "ats_output.json"
        
        with open("ats_output.json", 'w') as f:
            json.dump(ats_output, f, indent=2)
        print(f"   ✅ ATS processing complete")
    else:
        print("\n   ⚠️  No resume PDF provided, skipping ATS")
    
    # STEP 2: LinkedIn Processing
    if linkedin_pdf and os.path.exists(linkedin_pdf):
        print(f"\n💼 Processing LinkedIn: {linkedin_pdf}")
        parser = LinkedInPDFParser()
        linkedin_output = parser.parse_pdf(linkedin_pdf)
        evidence_files['linkedin'] = "linkedin_output.json"
        
        with open("linkedin_output.json", 'w') as f:
            json.dump(linkedin_output, f, indent=2)
        print(f"   ✅ LinkedIn processing complete")
    else:
        print("\n   ⚠️  No LinkedIn PDF provided, skipping")
    
    # STEP 3: GitHub Analysis
    if github_username:
        print(f"\n🐙 Analyzing GitHub: {github_username}")
        client = GitHubAPIClient(token=GITHUB_PAT)
        
        # Get user profile
        user_profile = client.get_user_profile(github_username)
        if not user_profile:
            print("   ❌ GitHub user not found")
        else:
            # Get repos
            repos = client.get_user_repos(github_username, max_repos=30)
            
            # Aggregate languages with framework detection
            language_analysis = client.aggregate_languages(github_username, repos)
            
            # Get best repositories
            best_repos = client.select_best_repositories(github_username, repos, top_n=5)
            
            # Calculate credibility
            credibility = client.calculate_credibility_score(user_profile)
            
            github_output = {
                "username": github_username,
                "profile": user_profile,
                "credibility": credibility,
                "languages": language_analysis,
                "best_repositories": best_repos,
                "scan_timestamp": "2026-01-27"
            }
            
            evidence_files['github'] = "github_output.json"
            with open("github_output.json", 'w') as f:
                json.dump(github_output, f, indent=2)
            print(f"   ✅ GitHub analysis complete")
    else:
        print("\n   ⚠️  No GitHub username provided, skipping")
    
    # STEP 4: LeetCode Scraping
    if leetcode_url:
        print(f"\n🎯 Scraping LeetCode: {leetcode_url}")
        leetcode_output = analyze_leetcode_profile(leetcode_url)
        
        if "error" in leetcode_output:
            print(f"   ❌ LeetCode error: {leetcode_output['error']}")
        else:
            # Normalize to evidence format
            leetcode_evidence = {
                "platform": "leetcode",
                "url": leetcode_url,
                "data": leetcode_output,
                "verified_language": leetcode_output.get("top_language"),
                "algorithmic_strength": "high" if leetcode_output.get("problems_solved", 0) > 200 else "moderate",
                "scan_timestamp": "2026-01-27"
            }
            
            evidence_files['leetcode'] = "leetcode_output.json"
            with open("leetcode_output.json", 'w') as f:
                json.dump(leetcode_evidence, f, indent=2)
            print(f"   ✅ LeetCode scraping complete")
    else:
        print("\n   ⚠️  No LeetCode URL provided, skipping")
    
    # STEP 5: Codeforces Scraping
    if codeforces_url:
        print(f"\n⚔️  Scraping Codeforces: {codeforces_url}")
        codeforces_output = analyze_codeforces_profile(codeforces_url)
        
        if "error" in codeforces_output:
            print(f"   ❌ Codeforces error: {codeforces_output['error']}")
        else:
            # Normalize to evidence format
            codeforces_evidence = {
                "platform": "codeforces",
                "url": codeforces_url,
                "data": codeforces_output,
                "verified_language": codeforces_output.get("top_language"),
                "competitive_strength": "elite" if codeforces_output.get("rating", 0) > 2400 else "high",
                "scan_timestamp": "2026-01-27"
            }
            
            evidence_files['codeforces'] = "codeforces_output.json"
            with open("codeforces_output.json", 'w') as f:
                json.dump(codeforces_evidence, f, indent=2)
            print(f"   ✅ Codeforces scraping complete")
    else:
        print("\n   ⚠️  No Codeforces URL provided, skipping")
    
    # STEP 6: Build Evidence Graph
    print(f"\n🧠 Building Evidence Graph...")
    builder = EvidenceGraphBuilder()
    
    # Load evidence files
    evidence_data = {}
    for source, filepath in evidence_files.items():
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                evidence_data[source] = json.load(f)
    
    # Build graph
    evidence_graph = builder.build_evidence_graph(evidence_data)
    
    with open("evidence_graph_output.json", 'w') as f:
        json.dump(evidence_graph, f, indent=2)
    print(f"   ✅ Evidence graph built")
    
    # STEP 7: Issue Credential
    print(f"\n🎓 Issuing Skill Credential...")
    agent = SkillVerificationAgent()
    credential = agent.issue_credential(evidence_graph)
    
    # Save final output
    with open(output_file, 'w') as f:
        json.dump(credential, f, indent=2)
    
    # Display result
    print("\n" + "="*60)
    print("🎓 SKILL CREDENTIAL ISSUED")
    print("="*60)
    print(json.dumps(credential, indent=2))
    print("\n" + "="*60)
    print("📊 DECISION SUMMARY")
    print("="*60)
    print(f"Status: {credential.get('credential_status')}")
    print(f"Verified Skills: {len(credential.get('verified_skills', []))}")
    print(f"Signal Strength: {credential.get('signal_strength')}")
    print(f"Test Required: {credential.get('test_required')}")
    print(f"Next Stage: {credential.get('next_stage')}")
    print()
    
    return credential


if __name__ == "__main__":
    # Example usage
    credential = run_complete_verification(
        resume_pdf="sample_resume.pdf",
        github_username="octocat",
        leetcode_url="https://leetcode.com/u/example/",
        codeforces_url="https://codeforces.com/profile/example"
    )
