"""
Complete Workflow Runner - Generates all evidence files from scratch

Usage:
    python run_complete_workflow.py --github USERNAME [--leetcode URL] [--codeforces URL] [--resume PDF]
"""
import sys
import os
import json
import subprocess
from pathlib import Path
import argparse
import uuid

# Fix import path to allow finding sibling agents
sys.path.append(str(Path(__file__).parent.parent))

# Add local directory for internal imports (Prioritized)
sys.path.insert(0, str(Path(__file__).parent))

def run_command(cmd, description):
    """Run a command and return JSON output"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return None
        
        # Try to extract JSON from output
        output = result.stdout
        
        # Find JSON in output (look for first { or [)
        json_start = -1
        for i, char in enumerate(output):
            if char in ['{', '[']:
                json_start = i
                break
        
        if json_start >= 0:
            try:
                json_data = json.loads(output[json_start:])
                print(f"✅ Success - Data extracted")
                return json_data
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Output is not valid JSON - {e}")
                print(f"   Output preview: {output[:200]}...")
                return None
        else:
            print(f"⚠️  Warning: No JSON found in output")
            return None
            
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run complete skill verification workflow")
    parser.add_argument("--github", required=True, help="GitHub username")
    parser.add_argument("--leetcode", help="LeetCode profile URL")
    parser.add_argument("--codeforces", help="Codeforces profile URL")
    parser.add_argument("--resume", help="Path to resume PDF")
    parser.add_argument("--linkedin", help="Path to LinkedIn PDF export")
    
    args = parser.parse_args()
    
    # Resolve absolute paths for files since subprocesses run in a different CWD
    if args.resume:
        args.resume = str(Path(args.resume).resolve())
    if args.linkedin:
        args.linkedin = str(Path(args.linkedin).resolve())
    
    # ORCHESTRATOR SIMULATION (Identity Split)
    import uuid
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    evaluation_id = f"eval_{uuid.uuid4().hex[:8]}"
    
    print("="*60)
    print("🚀 COMPLETE SKILL VERIFICATION WORKFLOW")
    print("="*60)
    print(f"\n🧠 PIPELINE ORCHESTRATOR")
    print(f"   User ID: {user_id}")
    print(f"   Evaluation ID: {evaluation_id}")
    
    pipeline_context = {
        "user_id": user_id,
        "evaluation_id": evaluation_id,
        "job_id": "job_123_software_engineer",
        "status": "initiated"
    }
    
    with open("pipeline_context.json", "w") as f:
        json.dump(pipeline_context, f, indent=2)
    print(f"   💾 Saved context to pipeline_context.json")

    print("\n📋 Pipeline Steps:")
    print("   1. ATS Resume Processing (MANDATORY)")
    print("   2. GitHub Analysis")
    print("   3. LeetCode Scraping (if provided)")
    print("   4. Codeforces Scraping (if provided)")
    print("   5. LinkedIn PDF Processing (if provided)")
    print("   6. Evidence Processing & Credential Issuance")

    
    # Step 1: ATS Resume (MANDATORY)
    ats_data = None
    if not args.resume:
        print("\n❌ Error: ATS Resume Processing is MANDATORY. Please provide --resume argument.")
        sys.exit(1)

    ats_data = run_command(
        f'python agents/ats.py "{args.resume}" --json-only --evaluation-id "{evaluation_id}" --email "{user_id}"',
        "Step 1: Processing ATS Resume (MANDATORY)"
    )
    
    if ats_data:
        if "error" in ats_data:
             print(f"\n❌ ATS Error: {ats_data.get('error')}")
             sys.exit(1)
             
        with open("ats_output.json", 'w', encoding='utf-8') as f:
            json.dump(ats_data, f, indent=2)
        print(f"   💾 Saved to ats_output.json")
        
        # Security/Review Check
        if ats_data.get("final_action") == "BLACKLISTED":
             print(f"\n❌ BLOCKED: Candidate Blacklisted by ATS")
             print(f"   Reason: {ats_data.get('human_review_reason')}")
             print(f"   Human Review ID: {ats_data.get('human_review_id')}")
             sys.exit(1)

        if ats_data.get("human_review_status") == "SUBMITTED":
             print(f"\n⚠️  Pipeline Paused: Human Review Required")
             print(f"   Review ID: {ats_data.get('human_review_id')}")
             print(f"   Reason: {ats_data.get('human_review_reason')}")
             sys.exit(0)
    else:
        print("\n❌ Error: ATS Processing validation failed. Stopping pipeline.")
        sys.exit(1)

    # Step 2: GitHub
    github_data = run_command(
        f"python scraper/github_api.py {args.github} --json-only",
        "Step 2: Analyzing GitHub Profile"
    )
    
    if github_data:
        with open("github_output.json", 'w', encoding='utf-8') as f:
            json.dump(github_data, f, indent=2)
        print(f"   💾 Saved to github_output.json")
    
    # Step 3: LeetCode
    leetcode_data = None
    if args.leetcode:
        leetcode_data = run_command(
            f'python scraper/leetcode_tool.py "{args.leetcode}"',
            "Step 3: Scraping LeetCode Profile"
        )
        
        if leetcode_data:
            with open("leetcode_output.json", 'w', encoding='utf-8') as f:
                json.dump(leetcode_data, f, indent=2)
            print(f"   💾 Saved to leetcode_output.json")
    
    # Step 4: Codeforces
    codeforces_data = None
    if args.codeforces:
        codeforces_data = run_command(
            f'python scraper/codeforce_tool.py "{args.codeforces}"',
            "Step 4: Scraping Codeforces Profile"
        )
        
        if codeforces_data:
            with open("codeforces_output.json", 'w', encoding='utf-8') as f:
                json.dump(codeforces_data, f, indent=2)
            print(f"   💾 Saved to codeforces_output.json")

    # Step 5: LinkedIn PDF (if provided)
    linkedin_data = None
    if args.linkedin:
        linkedin_data = run_command(
            f'python agents/linkedin_parser.py "{args.linkedin}" --json-only',
            "Step 5: Processing LinkedIn PDF"
        )
        
        if linkedin_data:
            with open("linkedin_output.json", 'w', encoding='utf-8') as f:
                json.dump(linkedin_data, f, indent=2)
            print(f"   💾 Saved to linkedin_output.json")

    
    # Step 6: Process Evidence
    print(f"\n{'='*60}")
    print(f"🧠 Step 6: Processing Evidence & Issuing Credential")
    print(f"{'='*60}")
    
    # Run from CWD (Root) so it can find the JSON files generated in this run
    script_path = Path(__file__).parent / "process_evidence.py"
    result = subprocess.run(
        f"python \"{script_path}\"",
        shell=True
        # cwd defaults to current process CWD (Root), which is where we saved the JSONs
    )
    
    if result.returncode == 0:
        print(f"\n{'='*60}")
        print(f"✅ WORKFLOW COMPLETE!")
        print(f"{'='*60}")
        print(f"\n📂 Generated Files:")
        print(f"   • pipeline_context.json")
        print(f"   • github_output.json")
        if args.leetcode:
            print(f"   • leetcode_output.json")
        if args.codeforces:
            print(f"   • codeforces_output.json")
        if args.resume:
            print(f"   • ats_output.json")
        print(f"   • evidence_graph_output.json")
        print(f"   • final_credential.json")
        
        print(f"\n📊 View results:")
        print(f"   cat final_credential.json")
    else:
        print(f"\n❌ Evidence processing failed")
        return

    # Step 8: Bias Detection (Stage 3 -> 4)
    print(f"\n{'='*60}")
    print(f"⚖️ Step 8: Bias Detection (System Audit)")
    print(f"{'='*60}")
    
    # Run Bias Agent (Importing direct to simulate)
    try:
        from bias_detection_agent.agents.bias_detection_agent import BiasDetectionAgent
        bias_agent = BiasDetectionAgent()
        bias_report = bias_agent.run_analysis(
            "final_credential.json", 
            mode="batch" # As per user requirement: Batch mode only
        )
        
        with open("bias_report.json", "w") as f:
            json.dump(bias_report, f, indent=2)
            
        print(f"   ✅ Bias Report Generated (Action: {bias_report.get('action')})")
    except Exception as e:
        print(f"   ❌ Bias Agent Error: {e}")
        return

    # Step 9: Transparent Matching (Stage 5)
    print(f"\n{'='*60}")
    print(f"🤝 Step 9: Transparent Matching")
    print(f"{'='*60}")
    
    try:
        from matching_agent.agents.matching_agent import MatchingAgent
        matching_agent = MatchingAgent()
        match_result = matching_agent.match_candidate(
            "final_credential.json",
            "bias_report.json",
            "matching_agent/data/mock_job_description.json",
            "pipeline_context.json"
        )
        
        with open("match_result.json", "w") as f:
            json.dump(match_result, f, indent=2)
            
        print(f"   ✅ Match Completed: Status={match_result.get('match_status')}, Score={match_result.get('match_score')}")
    except Exception as e:
        print(f"   ❌ Matching Agent Error: {e}")
        return

    # Step 10: Passport Agent (Credential Issuance)
    print(f"\n{'='*60}")
    print(f"🛂 Step 10: Passport Issuance (Finalize)")
    print(f"{'='*60}")
    
    try:
        from passport_agent.agents.passport_agent import PassportAgent
        
        # Load necessary inputs
        with open("final_credential.json", "r") as f:
            valid_skill_envelope = json.load(f)
            
        # Create Evaluation Bundle
        bundle = {
            "context": pipeline_context,
            "skill_verification": valid_skill_envelope,
            "bias_report": bias_report,
            "matching_result": match_result
        }
        
        passport_agent = PassportAgent()
        passport_result = passport_agent.create_passport(bundle)
        
        with open("passport_credential.json", "w") as f:
            json.dump(passport_result, f, indent=2)
            
        print(f"   ✅ PASSPORT SUCESSFULLY ISSUED!")
        print(f"   🆔 Credential ID: {passport_result.get('credential_id')}")
        print(f"   🔗 Verification: {passport_result.get('verification_url')}")
        
    except Exception as e:
        print(f"   ❌ Passport Error: {e}")
        return

    print(f"\n{'='*60}")
    print(f"🏆 PIPELINE EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"1. Identity: {user_id} | Eval: {evaluation_id}")
    print(f"2. Verified: {len(valid_skill_envelope.get('output', {}).get('verified_skills', {}).get('core',[]))} Core Skills")
    print(f"3. Bias Audit: {bias_report.get('bias_scope')} (Impact: {bias_report.get('candidate_impact')})")
    print(f"4. Match: {match_result.get('match_status')} ({match_result.get('match_score')}/100)")
    print(f"5. Passport: ISSUED (Signed)")
    print(f"   path: passport_credential.json")

if __name__ == "__main__":
    main()
