import sys
import json
import time
from curl_cffi import requests

def get_leetcode_data(username: str):
    """
    Fetches LeetCode data using rotation of browser fingerprints 
    to bypass strict Cloudflare timeouts.
    """
    url = "https://leetcode.com/graphql"
    
    # The Query
    query = """
    query userProfile($username: String!) {
      matchedUser(username: $username) {
        username
        profile { ranking }
        submitStats: submitStatsGlobal {
          acSubmissionNum { difficulty, count }
        }
        languageProblemCount { languageName, problemsSolved }
        badges { id, name }
        tagProblemCounts {
          advanced { tagName, problemsSolved }
          intermediate { tagName, problemsSolved }
        }
      }
      userContestRanking(username: $username) {
        rating
        globalRanking
        badge { name }
      }
    }
    """
    
    # 🛡️ FINGERPRINT ROTATION LIST
    # If Chrome fails, we try Safari, then Edge.
    fingerprints = [
        "chrome124",    # Newest Chrome
        "safari17_0",   # MacOS Safari
        "edge101",      # Microsoft Edge
        "chrome110"     # Older Chrome (Fallback)
    ]

    for browser in fingerprints:
        try:
            print(f"🔄 Trying connection as {browser}...")
            
            response = requests.post(
                url, 
                json={"query": query, "variables": {"username": username}}, 
                headers={
                    "Referer": f"https://leetcode.com/{username}/",
                    "Content-Type": "application/json",
                    "Origin": "https://leetcode.com"
                },
                impersonate=browser, 
                timeout=15  # Extended timeout
            )
            
            # If we get a valid response, break the loop and process
            if response.status_code == 200:
                print(f"✅ Success with {browser}!")
                return parse_response(response.json())
            
            elif response.status_code == 429:
                print(f"⚠️ Rate limited ({browser}). Waiting 2s...")
                time.sleep(2)
            else:
                print(f"❌ Failed with {browser} (Status: {response.status_code})")

        except Exception as e:
            print(f"❌ Timeout/Error with {browser}: {str(e)}")
            continue # Try next browser

    return {"error": "All browser fingerprints failed. LeetCode is blocking this IP."}

def parse_response(data):
    """Parses the raw JSON into our clean format"""
    if "errors" in data:
        return {"error": "User not found."}

    user = data.get("data", {}).get("matchedUser")
    if not user:
        return {"error": "User not found or profile is private."}

    contest = data.get("data", {}).get("userContestRanking")

    # 1. Skills
    final_skills = []
    if user.get("tagProblemCounts"):
        adv = sorted(user["tagProblemCounts"]["advanced"], key=lambda x: x['problemsSolved'], reverse=True)
        inter = sorted(user["tagProblemCounts"]["intermediate"], key=lambda x: x['problemsSolved'], reverse=True)
        final_skills = [f"{t['tagName']} (Adv)" for t in adv[:3]] + [t['tagName'] for t in inter[:3]]

    # 2. Top Language
    top_lang = "N/A"
    langs = sorted(user.get("languageProblemCount", []), key=lambda x: x['problemsSolved'], reverse=True)
    if langs: top_lang = langs[0]['languageName']

    # 3. Solved Count
    solved_count = 0
    for s in user.get("submitStats", {}).get("acSubmissionNum", []):
        if s['difficulty'] == "All":
            solved_count = s['count']
            break

    # 4. Rank & Level
    level_str = contest['badge']['name'] if (contest and contest.get('badge')) else "N/A"
    global_rank = user['profile']['ranking']

    return {
        "rank": f"{global_rank}",
        "level": level_str,
        "contest_rating": int(contest['rating']) if contest else 0,
        "problems_solved": solved_count,
        "top_skills": final_skills,
        "top_language": top_lang,
        "badges": len(user.get("badges", []))
    }

def analyze_leetcode_profile(url: str):
    if "leetcode.com" not in url:
        return {"error": "Invalid URL"}
    parts = url.rstrip("/").split("/")
    username = parts[-1]
    
    print(f"🕵️  Fetching data for user: {username}")
    return get_leetcode_data(username)

# RUNNABLE BLOCK
if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else input("Enter LeetCode URL: ")
    print(json.dumps(analyze_leetcode_profile(test_url), indent=2))