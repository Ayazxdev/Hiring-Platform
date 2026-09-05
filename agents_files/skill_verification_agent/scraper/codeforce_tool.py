import sys
import json
from collections import Counter
from curl_cffi import requests

def get_codeforces_data(handle: str):
    """
    Fetches Codeforces data using the official API.
    Fixes:
    - Captures Gym/Mashup problems by using flexible ID generation.
    - Fetches deep history (up to 100k submissions).
    """
    
    # 1. Fetch Basic Profile Info
    user_url = f"https://codeforces.com/api/user.info?handles={handle}"
    
    # 2. Fetch Submissions
    # We ask for a huge number to ensure we get everything.
    status_url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=100000"

    try:
        # --- REQUEST 1: PROFILE ---
        resp_user = requests.get(user_url, impersonate="chrome110", timeout=10)
        if resp_user.status_code != 200:
            return {"error": f"Codeforces API Error: {resp_user.status_code}"}
        
        user_data = resp_user.json()
        if user_data["status"] != "OK":
            return {"error": "User not found."}
            
        user = user_data["result"][0]

        # --- REQUEST 2: SUBMISSIONS ---
        resp_status = requests.get(status_url, impersonate="chrome110", timeout=30)
        subs_data = resp_status.json()
        
        unique_solved = set()
        all_tags = []
        languages = []
        
        if subs_data["status"] == "OK":
            for sub in subs_data["result"]:
                # 1. STRICT VERDICT CHECK: Only accept "OK" (Green/Accepted)
                if sub.get("verdict") == "OK":
                    problem = sub.get("problem", {})
                    
                    # 2. ROBUST ID GENERATION
                    # Standard problems have contestId + index (e.g., 123A)
                    # Gym problems might rely on name.
                    # We create a composite key to ensure we count EVERYTHING unique.
                    
                    cid = str(problem.get("contestId", "Gym"))
                    idx = problem.get("index", "")
                    name = problem.get("name", "Unknown")
                    
                    # Key: "123-A-Watermelon" or "Gym-Watermelon"
                    # This prevents skipping problems that lack an ID
                    prob_id = f"{cid}-{idx}-{name}"
                    
                    if prob_id not in unique_solved:
                        unique_solved.add(prob_id)
                        
                        # Collect Stats
                        all_tags.extend(problem.get("tags", []))
                        languages.append(sub.get("programmingLanguage"))

        # --- DATA ANALYSIS ---
        
        # 1. Top Skills (Top 5)
        top_skills = []
        if all_tags:
            # Filter out very generic tags if needed, or keep them all.
            top_skills_counts = Counter(all_tags).most_common(5)
            top_skills = [tag[0] for tag in top_skills_counts]

        # 2. Top Language
        top_lang = "N/A"
        if languages:
            top_lang = Counter(languages).most_common(1)[0][0]

        return {
            "rank": user.get("rank", "Unrated").title(),
            "rating": user.get("rating", 0),
            "max_rating": user.get("maxRating", 0),
            "problems_solved": len(unique_solved),
            "top_skills": top_skills,
            "top_language": top_lang,
            "organization": user.get("organization", "N/A"),
            "contribution": user.get("contribution", 0)
        }

    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def analyze_codeforces_profile(url: str):
    # Handle cleaning
    if "codeforces.com" in url:
        parts = url.rstrip("/").split("/")
        if "profile" in parts:
            idx = parts.index("profile")
            if idx + 1 < len(parts):
                handle = parts[idx + 1]
            else:
                return {"error": "Invalid Profile URL"}
        else:
            handle = parts[-1]
    else:
        handle = url

    print(f"🕵️  Fetching Codeforces data for: {handle}")
    return get_codeforces_data(handle)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else input("Enter Codeforces URL or Handle: ")
    print(json.dumps(analyze_codeforces_profile(target), indent=2))