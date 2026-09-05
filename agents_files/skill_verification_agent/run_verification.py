"""
Simple Runner for Complete Skill Verification

Usage:
    python run_verification.py --github USERNAME [--leetcode URL] [--codeforces URL] [--resume PDF] [--linkedin PDF]

Example:
    python run_verification.py --github example_user --leetcode https://leetcode.com/u/example/
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.github_api import GitHubAPIClient
from scraper.leetcode_tool import analyze_leetcode_profile
from scraper.codeforce_tool import analyze_codeforces_profile
from agents.evidence_graph_builder import EvidenceGraphBuilder
from agents.skill_verification_agent_v2 import SkillVerificationAgentV2
from config import GITHUB_PAT

def main():
    parser = argparse.ArgumentParser(description="Run complete skill verification")
    parser.add_argument("--github", help="GitHub username")
    parser.add_argument("--leetcode", help="LeetCode profile URL")
    parser.add_argument("--codeforces", help="Codeforces profile URL")
    parser.add_argument("--resume", help="Path to resume PDF")
    parser.add_argument("--linkedin", help="Path to LinkedIn PDF")
    parser.add_argument("--output", default="final_result.json", help="Output file")
    
    args = parser.parse_args()
    
    if not args.github:
        print("❌ GitHub username is required!")
        print("Usage: python run_verification.py --github USERNAME")
        sys.exit(1)
    
    print("="*60)
    print("🚀 SKILL VERIFICATION PIPELINE")
    print("="*60)
    
    evidence_data = {}
    
    # GitHub Analysis
    if args.github:
        print(f"\n🐙 Analyzing GitHub: {args.github}")
        client = GitHubAPIClient(token=GITHUB_PAT)
        
        # Get user profile
        user_profile = client.get_user_profile(args.github)
        if not user_profile:
            print("   ❌ GitHub user not found")
        else:
            # Get repos
            repos = client.get_user_repos(args.github, max_repos=30)
            
            # Aggregate languages
            language_analysis = client.aggregate_languages(args.github, repos)
            
            # Get best repositories
            best_repos = client.select_best_repositories(args.github, repos, top_n=5)
            
            # Calculate credibility
            credibility = client.calculate_credibility_score(user_profile)
            
            # Get commit activity
            commit_activity = client.get_commit_activity(args.github, repos)
            
            github_output = {
                "username": args.github,
                "profile": user_profile,
                "credibility": credibility,
                "languages": language_analysis,
                "best_repositories": best_repos,
                "commit_activity": commit_activity
            }
            
            evidence_data['github'] = github_output
            print(f"   ✅ GitHub analysis complete")
    
    # LeetCode Scraping
    if args.leetcode:
        print(f"\n🎯 Scraping LeetCode: {args.leetcode}")
        leetcode_output = analyze_leetcode_profile(args.leetcode)
        
        if "error" in leetcode_output:
            print(f"   ❌ LeetCode error: {leetcode_output['error']}")
        else:
            evidence_data['leetcode'] = leetcode_output
            print(f"   ✅ LeetCode scraping complete")
    
    # Codeforces Scraping
    if args.codeforces:
        print(f"\n⚔️  Scraping Codeforces: {args.codeforces}")
        codeforces_output = analyze_codeforces_profile(args.codeforces)
        
        if "error" in codeforces_output:
            print(f"   ❌ Codeforces error: {codeforces_output['error']}")
        else:
            evidence_data['codeforces'] = codeforces_output
            print(f"   ✅ Codeforces scraping complete")
    
    # Build Evidence Graph
    print(f"\n🧠 Building Evidence Graph...")
    builder = EvidenceGraphBuilder()
    
    # Call with proper parameters in correct order
    # Pass competitive programming data (codeforces) into graph builder
    evidence_graph = builder.build_evidence_graph(
        ats_output=None,  # No ATS data yet
        linkedin_output=None,  # No LinkedIn data yet
       github_output=evidence_data.get('github'),
        leetcode_output=evidence_data.get('leetcode'),
        codechef_output=evidence_data.get('codeforces')  # Using codeforces for now
    )
    
    with open("evidence_graph_output.json", 'w') as f:
        json.dump(evidence_graph, f, indent=2)
    print(f"   ✅ Evidence graph built")
    
    # Issue Credential
    print(f"\n🎓 Issuing Skill Credential...")
    agent = SkillVerificationAgentV2()
    credential = agent.issue_credential(evidence_graph)
    
    # Save final output
    with open(args.output, 'w') as f:
        json.dump(credential, f, indent=2, default=str)
    
    # Display result
    print("\n" + "="*60)
    print("🎓 SKILL CREDENTIAL ISSUED")
    print("="*60)
    print(json.dumps(credential, indent=2, default=str))
    print("\n" + "="*60)
    print("📊 DECISION SUMMARY")
    print("="*60)
    print(f"Status: {credential.get('credential_status')}")
    print(f"Verified Skills: {len(credential.get('verified_skills', []))}")
    print(f"Skill Confidence: {credential.get('skill_confidence', 0)}")
    print(f"Signal Strength: {credential.get('signal_strength')}")
    print(f"Test Required: {credential.get('test_required')}")
    print(f"Next Stage: {credential.get('next_stage')}")
    print()

if __name__ == "__main__":
    main()
