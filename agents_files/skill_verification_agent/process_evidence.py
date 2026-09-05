"""
Skill Verification Agent - Evidence Processor

Reads pre-generated evidence JSON files and issues credential.

Usage:
    python process_evidence.py

Expected input files:
    - github_output.json (optional)
    - ats_output.json (optional)
    - linkedin_output.json (optional)
    - leetcode_output.json (optional)
    - codeforces_output.json (optional)

Output:
    - evidence_graph_output.json
    - final_credential.json
"""
import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.evidence_graph_builder import EvidenceGraphBuilder
from agents.skill_verification_agent_v2 import SkillVerificationAgentV2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_json_if_exists(filepath: str):
    """Load JSON file if it exists, return None otherwise"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {filepath}: {e}")
            return None
    return None

def main():
    print("="*60)
    print("🧠 SKILL VERIFICATION - EVIDENCE PROCESSOR")
    print("="*60)
    
    # Load all evidence files
    print("\n📂 Loading evidence files...")
    
    github_data = load_json_if_exists("github_output.json")
    ats_data = load_json_if_exists("ats_output.json")
    linkedin_data = load_json_if_exists("linkedin_output.json")
    leetcode_data = load_json_if_exists("leetcode_output.json")
    codeforces_data = load_json_if_exists("codeforces_output.json")
    
    # Report what was found
    sources_found = []
    if github_data:
        sources_found.append("✅ GitHub")
    else:
        print("   ⚠️  github_output.json not found")
    
    if ats_data:
        sources_found.append("✅ ATS Resume")
    else:
        print("   ⚠️  ats_output.json not found")
    
    if linkedin_data:
        sources_found.append("✅ LinkedIn")
    else:
        print("   ⚠️  linkedin_output.json not found")
    
    if leetcode_data:
        sources_found.append("✅ LeetCode")
    else:
        print("   ⚠️  leetcode_output.json not found")
    
    if codeforces_data:
        sources_found.append("✅ Codeforces")
    else:
        print("   ⚠️  codeforces_output.json not found")
    
    if not sources_found:
        print("\n❌ ERROR: No evidence files found!")
        print("\nPlease generate evidence files first:")
        print("  - Run: python scraper/github_api.py USERNAME > github_output.json")
        print("  - Run: python agents/ats.py resume.pdf > ats_output.json")
        print("  - Run: python scraper/leetcode_tool.py URL > leetcode_output.json")
        print("  - Run: python scraper/codeforce_tool.py URL > codeforces_output.json")
        sys.exit(1)
    
    print(f"\n📊 Found {len(sources_found)} evidence sources:")
    for source in sources_found:
        print(f"   {source}")
    
    # Build Evidence Graph
    # Build Evidence Graph
    print(f"\n🧠 Building Evidence Graph...")
    
    # Load pipeline context for evaluation_id
    context = load_json_if_exists("pipeline_context.json")
    evaluation_id = context.get("evaluation_id") if context else None
    if evaluation_id:
        print(f"   🔑 Process Context: {evaluation_id}")
    else:
        print(f"   ⚠️ No pipeline context found - using legacy mode")

    builder = EvidenceGraphBuilder()
    
    evidence_graph = builder.build_evidence_graph(
        ats_output=ats_data,
        linkedin_output=linkedin_data,
        github_output=github_data,
        leetcode_output=leetcode_data,
        codechef_output=codeforces_data, # Using codeforces data for codechef param
        evaluation_id=evaluation_id
    )
    
    # Save evidence graph
    with open("evidence_graph_output.json", 'w') as f:
        json.dump(evidence_graph, f, indent=2)
    print(f"   ✅ Evidence graph saved → evidence_graph_output.json")
    
    # Issue Credential
    print(f"\n🎓 Issuing Skill Credential...")
    agent = SkillVerificationAgentV2()
    credential_envelope = agent.issue_credential(evidence_graph)
    
    # Unwrap for usage here, but save the full envelope
    if "output" in credential_envelope:
        credential_data = credential_envelope["output"]
    else:
        credential_data = credential_envelope # Should not happen with new V2 agent
    
    # Save final credential (THE ENVELOPE)
    with open("final_credential.json", 'w') as f:
        json.dump(credential_envelope, f, indent=2, default=str)
    print(f"   ✅ Credential saved → final_credential.json")
    
    # Display result
    print("\n" + "="*60)
    print("🎓 SKILL CREDENTIAL ISSUED")
    print("="*60)
    print(json.dumps(credential_envelope, indent=2, default=str))
    
    print("\n" + "="*60)
    print("📊 DECISION SUMMARY")
    print("="*60)
    print(f"Status: {credential_data.get('credential_status')}")
    # Handle tiered skills display
    skills = credential_data.get('verified_skills', [])
    if isinstance(skills, dict):
        # Flatten for count
        count = sum(len(v) for v in skills.values())
        print(f"Verified Skills: {count} (Tiered)")
    else:
        print(f"Verified Skills: {len(skills)}")
        
    print(f"Skill Confidence: {credential_data.get('skill_confidence', 0)}")
    print(f"Signal Strength: {credential_data.get('signal_strength')}")
    print(f"Test Required: {credential_data.get('test_required')}")
    print(f"Next Stage: {credential_data.get('next_stage')}")
    print()

if __name__ == "__main__":
    main()
