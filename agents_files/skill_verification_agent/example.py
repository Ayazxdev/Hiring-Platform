"""
Skill Verification Agent - Interactive Tester

Run this script to test the agent with your own profile URLs.
"""
import json
import logging
from agents.skill_verification_agent import SkillVerificationAgent

# Configure logging to show progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_user_input():
    """Get profile links from user"""
    print("\n" + "="*60)
    print("SKILL VERIFICATION AGENT - TESTER")
    print("="*60)
    print("Please paste your profile URLs (press Enter to skip):")
    
    email = input("Email [test@example.com]: ").strip() or "test@example.com"
    github_url = input("GitHub URL: ").strip()
    leetcode_url = input("LeetCode URL: ").strip()
    codechef_url = input("CodeChef URL: ").strip()
    linkedin_pdf = input("LinkedIn PDF Path (optional): ").strip()
    resume_text = input("Resume Text (short summary): ").strip() or "Experienced Python developer"
    
    return {
        "email": email,
        "github_url": github_url,
        "leetcode_url": leetcode_url,
        "codechef_url": codechef_url,
        "linkedin_pdf": linkedin_pdf,
        "resume": resume_text
    }

def run_agent():
    # 1. Get User Input
    user_data = get_user_input()
    
    if not user_data["github_url"] and not user_data["leetcode_url"] and not user_data["linkedin_pdf"]:
        print("\n❌ Error: Please provide at least one profile URL or LinkedIn PDF.")
        return

    # 2. Initialize Agent
    print("\n🚀 Initializing Agent...")
    try:
        agent = SkillVerificationAgent()
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        print("Tip: Make sure Ollama or OpenRouter is configured in config.py")
        return

    # 3. Create Application Packet
    application = {
        "name": "Test Candidate",
        "email": user_data["email"],
        "resume": user_data["resume"],
        "gender": "Unknown",
        "college": "Unknown"
    }
    
    # 4. Run Verification
    print("\n🔍 Starting Verification Pipeline...")
    credential = agent.scrape_and_verify(
        application=application,
        github_url=user_data["github_url"] or None,
        leetcode_url=user_data["leetcode_url"] or None,
        codechef_url=user_data["codechef_url"] or None,
        linkedin_pdf_path=user_data["linkedin_pdf"] or None,
        save_profile=True,
        output_dir="."
    )
    
    # 5. Show Result
    print("\n" + "="*60)
    print("✅ FINAL CREDENTIAL ISSUED")
    print("="*60)
    print(json.dumps(credential, indent=2, default=str))
    
    print("\n📁 Artifacts saved:")
    print(f"- Credential ID: {credential['credential_id']}")
    print("- Full profile JSON saved in current directory")

if __name__ == "__main__":
    run_agent()