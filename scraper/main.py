import streamlit as st
import pandas as pd
import json
from scrape import (
    scrape_dynamic_page, 
    identify_platform, 
    scrape_website, 
    get_contribution_history, 
    get_contribution_count, 
    get_total_lifetime_contributions,
    get_project_details,
    get_smart_main_files,
    get_file_content,
    scrape_multiple_profiles
)
from parse import parse_with_ollama

st.set_page_config(page_title="AI Profile Auditor", layout="wide")
st.title("🕵️ Universal Candidate Auditor")

# NAVIGATION TABS
tab1, tab2, tab3 = st.tabs(["👤 Profile Analyzer", "📂 Project Rater", "🚀 Batch Processor"])

# TAB 1: UNIVERSAL PROFILE
with tab1:
    url = st.text_input("Enter Profile URL (GitHub, LinkedIn, LeetCode, Codeforces)", 
                   placeholder="https://github.com/torvalds")

    # 1. INITIALIZE SESSION STATE
    if "profile_data" not in st.session_state:
        st.session_state.profile_data = None
    if "platform" not in st.session_state:
        st.session_state.platform = None

    # 2. TRIGGER ANALYSIS (Scraping Layer)
    if st.button("🔍 Analyze Profile"):
        if url:
            # RESET old AI results to prevent showing cached data for wrong user
            if "ai_result" in st.session_state:
                del st.session_state.ai_result
            
            platform = identify_platform(url)
            st.session_state.platform = platform
            st.info(f"Detected Platform: **{platform}**")
            
            # Handle GitHub profile scraping
            if platform == "GitHub":
                with st.spinner("Scraping GitHub Data..."):
                    dom_content = scrape_website(url)
                    st.session_state.profile_data = {
                        "dom_content": dom_content,
                        "stats": get_contribution_history(dom_content),
                        "header_count": get_contribution_count(dom_content),
                        "username": url.strip("/").split("/")[-1]
                    }

            # SCENARIO B: OTHERS (LeetCode, LinkedIn, etc.)
            else:
                with st.spinner(f"Scraping {platform}..."):
                    # This runs the specialized scroller for LeetCode/LinkedIn
                    data = scrape_dynamic_page(url, platform)
                    st.session_state.profile_data = data

    # 3. DISPLAY RESULTS (UI Layer - Runs on every reload)
    if st.session_state.profile_data:
        platform = st.session_state.platform
        data = st.session_state.profile_data
        

        # OPTION A: GITHUB DISPLAY

        if platform == "GitHub":
            stats = data["stats"]
            username = data["username"]
            
            st.success(f"✅ GitHub Header Says: {data['header_count']}")
            
            if st.button("📊 Calculate Lifetime Contributions"):
                with st.spinner("Summing up all years..."):
                    total = get_total_lifetime_contributions(username)
                    st.metric("Total Lifetime Contributions", total)

            if "error" not in stats:
                st.divider()
                st.subheader("📅 Activity Timeline")
                if stats['monthly_log']:
                    monthly_df = pd.DataFrame(list(stats['monthly_log'].items()), columns=['Month', 'Commits'])
                    st.bar_chart(monthly_df.set_index('Month'))
                
                if st.button("🧠 Run AI Consistency Check"):
                    prompt = (
                        "You are a Senior Engineering Recruiter and Technical Evaluator specializing in assessing developer consistency, reliability, and growth trends from GitHub activity data.\n"
                            "You will be given a JSON summary of a developer’s GitHub commit history. Your task is to analyze this data and evaluate coding consistency, not raw volume.\n\n"
                            
                            f"--- CANDIDATE DATA ---\n"
                            f"Observation Period: {stats['period']}\n"
                            f"Total Commits (Year): {stats['total_commits']}\n"
                            f"Max Gap: {stats['max_gap']} days\n"
                            f"Recent Activity (Last 30 Days): {stats['commits_last_30_days']}\n"
                            f"Days Since Last Commit: {stats['days_since_last_commit']}\n"
                            f"Monthly Breakdown: {stats['monthly_log']}\n\n"

                            "--- CORE EVALUATION PRINCIPLE (CRITICAL) ---\n"
                            "Recent behavior is more important than historical behavior.\n"
                            "Weight the most recent 2–3 months more heavily than older activity. Do NOT penalize developers for past inactivity if recent consistency is strong.\n\n"

                            "--- SCORING LOGIC (0–10) ---\n"
                            "10: Flawless daily consistency.\n"
                            "8-9: Strong recent consistency (Recently active) OR predictable weekly patterns.\n"
                            "5-7: Generally consistent but with noticeable recent gaps.\n"
                            "1-4: Highly irregular, sporadic, or currently inactive.\n\n"

                            "--- REQUIRED PERSONAS (Choose exactly one) ---\n"
                            " Veteran — Consistent contributions across most of the year.\n"
                            " Recently active — Low/no activity earlier, but strong, sustained recent consistency.\n"
                            " Burnout — Previously consistent, but little/no activity in last 1–2 months.\n"
                            " Sporadic — Irregular activity with frequent gaps.\n"
                            " Inactive — Minimal activity.\n\n"

                            "--- MANDATORY EDGE-CASE HANDLING ---\n"
                            "1. Rising Star: Long early inactivity followed by daily recent commits → HIGH score (8/10).\n"
                            "2. Burnout: Strong history but zero recent commits → LOW score.\n"
                            "3. Weekend Warrior: Commits only on weekends but never misses → Consistent (Veteran).\n\n"

                            "--- OUTPUT RULES (STRICT) ---\n"
                            "Return the result in this exact format and everything should be in separate line:\n"
                            "Score: [0–10]\n"
                            "Persona: [Veteran | Recently active | Burnout | Sporadic | Inactive]\n"
                            "Reasoning: [One clear, single-sentence explanation focused on recency and pattern]"
                    )
                    with st.spinner("AI is analyzing habits..."):
                        res = parse_with_ollama([prompt], "Consistency Check")
                        st.info(res)

            # Handle other platforms (LeetCode, LinkedIn, etc.)
            else:
                with st.spinner(f"Scraping {platform}..."):
                    data = scrape_dynamic_page(url, platform)
                    st.session_state.profile_data = data

    # 3. DISPLAY RESULTS (UI Layer)
    if st.session_state.profile_data:
        platform = st.session_state.platform
        data = st.session_state.profile_data
        
        # Render GitHub stats and charts
        if platform == "GitHub":
            # (Keep your existing GitHub display code here...)
            # ... (stats, header_count, chart, etc.) ...
            # ... (Stop before the 'else' block) ...
            stats = data["stats"]
            username = data["username"]
            
            st.success(f"✅ GitHub Header Says: {data['header_count']}")
            
            if st.button("📊 Calculate Lifetime Contributions"):
                with st.spinner("Summing up all years..."):
                    total = get_total_lifetime_contributions(username)
                    st.metric("Total Lifetime Contributions", total)

            if "error" not in stats:
                st.divider()
                st.subheader("📅 Activity Timeline")
                if stats['monthly_log']:
                    monthly_df = pd.DataFrame(list(stats['monthly_log'].items()), columns=['Month', 'Commits'])
                    st.bar_chart(monthly_df.set_index('Month'))
                
                if st.button("🧠 Run AI Consistency Check"):
                    prompt = (
                        "You are a Senior Engineering Recruiter. Analyze this GitHub activity.\n"
                        f"Stats: {stats}\n"
                        "Verdict: Is this candidate consistent? (Score 0-10)"
                    )
                    with st.spinner("AI is analyzing habits..."):
                        res = parse_with_ollama([prompt], "Consistency Check")
                        st.info(res)


        # OPTION B: OTHER PLATFORMS DISPLAY 

        else:
            if "error" in data:
                st.error(f"Scraping Failed: {data['error']}")
            else:
                raw_text = data['content']
                st.subheader(f"📊 {platform} Analysis")
                
                # PROMPT SELECTION
                if platform == "LinkedIn":
                    prompt = f"Extract Experience & Skills from:\n{raw_text[:15000]}"
                    task = "LinkedIn Extraction"
                
                elif platform == "LeetCode":
                    prompt = (
                        "You are a specialized Data Extraction Engine designed to parse unstructured developer profiles. "
                        "Your goal is to extract raw metrics while strictly ignoring percentages.\n\n"

                        f"--- INPUT TEXT START ---\n"
                        f"{raw_text[:20000]}\n"
                        f"--- INPUT TEXT END ---\n\n"

                        "--- EXTRACTION TASKS & HEURISTICS ---\n"
                        "1. RANK / RATING\n"
                        "   - Target Keywords: 'Rank', 'Global Rank', 'Tier'.\n"
                        "   - Priority 1: Look for titles (e.g., 'Guardian', 'Knight', 'Master').\n"
                        "   - Priority 2: Look for ranking numbers (e.g., '12,405', '~4,000,000').\n"
                        "   - If 'Unrated', return 'Unrated'.\n\n"

                        "2. PROBLEMS SOLVED (CRITICAL: Ignore Percentages)\n"
                        "   - Rule: You will see text like 'Solved 100%' or 'Beats 95%'. IGNORE THESE.\n"
                        "   - Target Pattern: Look for the specific fraction format 'X / Y' (e.g., '1 / 3817' or '450 / 2000').\n"
                        "   - Action: Extract only the number 'X' (the numerator).\n"
                        "   - Fallback: If no fraction exists, look for 'Problems Solved: X'.\n\n"

                        "3. TOP LANGUAGE\n"
                        "   - Scan the 'Languages' section.\n"
                        "   - Identify the language with the HIGHEST usage count or problems solved.\n"
                        "   - Return ONLY the name (e.g., 'Python').\n\n"

                        "4. BADGES\n"
                        "   - Look for the word 'Badges'. Extract the count immediately following it or count the listed items.\n\n"

                        "5. CONTEST RATING METRICS (Strict Validation)\n"
                        "   - Target: Look for the exact label 'Contest Rating' followed by a number.\n"
                        "   - Action: Extract that number.\n"
                        "   - CRITICAL CONSTRAINT: Do NOT use the total problem count (the 'Y' in 'X / Y') as the rating. The number 3000+ is usually the total questions, NOT the rating.\n"
                        "   - Fallback: If the phrase 'Contest Rating' is NOT found, strictly return 'Contest Rating not available on profile page'.\n\n"

                        "6. TOPIC STRENGTHS (Specialist Filter)\n"
                        "   - Context: Look for the 'Skills' section in the text.\n"
                        "   - Action: Extract ONLY the skill names that are explicitly labeled as 'Advanced' or 'Intermediate'.\n"
                        "   - Exclusion: Strictly IGNORE any skills labeled as 'Fundamental', 'Beginner', or 'Novice'.\n"
                        "   - Output: A single flat list of strings (e.g., ['Dynamic Programming', 'System Design']).\n\n"

                        "--- RESPONSE FORMAT (Strict JSON) ---\n"
                        "{\n"
                        "  \"rank\": \"String\",\n"
                        "  \"problems_solved\": Integer,\n"
                        "  \"top_language\": \"String\",\n"
                        "  \"badges\": Integer,\n"
                        "  \"contest_rating\": \"String\",\n"
                        "  \"max_rating\": Integer,\n"
                        "  \"top_skills\": [\"String list\"]\n"
                        "}"
                    )
                    task = "LeetCode Extraction"

                elif platform == "CodeChef":
                    prompt = (
                        "You are a specialized Data Extraction Engine designed to parse unstructured CodeChef developer profiles. "
                        "Your goal is to extract raw metrics while strictly ignoring percentages.\n\n"

                        f"--- INPUT TEXT START ---\n"
                        f"{raw_text[:20000]}\n"
                        f"--- INPUT TEXT END ---\n\n"

                        "--- EXTRACTION TASKS & HEURISTICS ---\n"
                        "1. RANK / RATING\n"
                        "   - Target Keywords: 'Global Rank', 'Country Rank'.\n"
                        "   - Priority 1: Look for the 'Global Rank' number (e.g., '165,908' or '2000').\n"
                        "   - Priority 2: Look for the 'Division' label (e.g., 'Div 1', 'Div 2', 'Div 3', 'Div 4').\n"
                        "   - Action: Combine them if found (e.g., '165,908 (Div 4)'). If 'Unrated', return 'Unrated'.\n\n"

                        "2. PROBLEMS SOLVED (CRITICAL: Ignore Percentages)\n"
                        "   - Rule: Ignore 'Top X%' or heat map participation percentages.\n"
                        "   - Target Pattern: Look for 'Fully Solved (X)' or 'Total Problems Solved: X'.\n"
                        "   - Action: Extract the integer X.\n"
                        "   - Fallback: If 'Fully Solved' is missing, sum the 'Practice' and 'Compete' problem counts if visible.\n\n"

                        "3. TOP LANGUAGE\n"
                        "   - Scan the 'Recent Activity' or 'Language' breakdown sections.\n"
                        "   - Identify the language with the HIGHEST usage count or most recent submissions.\n"
                        "   - Return ONLY the name (e.g., 'C++', 'Python').\n\n"

                        "4. BADGES\n"
                        "   - Look for the word 'Badges'. Count the named badges listed (e.g., 'Code Enthusiast', 'Problem Solver').\n"
                        "   - Action: Return the integer count of badges found.\n\n"

                        "5. CONTEST RATING METRICS (Strict Validation)\n"
                        "   - Target: Look for the large bold number in the Rating box (e.g., '917', '1600').\n"
                        "   - Stars: Look for the Star rating (e.g., '1★', '3★', '5★'). Append this to the rating string.\n"
                        "   - Max Rating: Look for 'Highest Rating' followed by a number.\n"
                        "   - CRITICAL CONSTRAINT: Do NOT confuse 'Global Rank' (usually large, e.g., 100,000+) with 'Rating' (usually 0-3500).\n"
                        "   - Fallback: If rating is not found, return 'Unrated'.\n\n"

                        "6. TOPIC STRENGTHS (Verified Skills)\n"
                        "   - Context: Look for 'Skill facts', 'Expertise', or 'Learning Paths' sections.\n"
                        "   - Action: Extract skills that appear to be verified (e.g., 'Python Skill test') or completed learning paths.\n"
                        "   - Exclusion: Ignore general text descriptions.\n"
                        "   - Output: A single flat list of strings.\n\n"

                        "--- RESPONSE FORMAT (Strict JSON) ---\n"
                        "{\n"
                        "  \"rank\": \"String\",\n"
                        "  \"problems_solved\": Integer,\n"
                        "  \"top_language\": \"String\",\n"
                        "  \"badges\": Integer,\n"
                        "  \"contest_rating\": \"String\",\n"
                        "  \"max_rating\": Integer,\n"
                        "  \"top_skills\": [\"String list\"]\n"
                        "}"
                    )
                    task = "CodeChef Extraction"

                elif platform == "Codeforces":
                    prompt = (
                        "You are a Codeforces Data Extractor.\n"
                        f"--- INPUT TEXT ---\n{raw_text[:15000]}\n------------------\n"
                        "Extract fields:\n"
                        "1. Rank: User Tier (e.g., 'Specialist').\n"
                        "2. Rating: Current Contest Rating (Integer).\n"
                        "3. Max Rating: Highest Rating ever achieved (Integer).\n"
                        "4. Problems Solved: 'All time solved'.\n"
                        "5. Top Language: Language with most submissions.\n"
                        "--- OUTPUT JSON ---\n"
                        "{ \"rank\": \"String\", \"contest_rating\": Int, \"max_rating\": Int, \"problems_solved\": Int, \"top_skills\": [\"List\"], \"top_language\": \"String\", \"badges\": Int }"
                    )
                    task = "Codeforces Extraction"

                else:
                    prompt = f"Summarize this profile: {raw_text[:5000]}"
                    task = "Generic Summary"

                # AUTO-RUN AI
                if "ai_result" not in st.session_state:
                     with st.spinner("🤖 AI is extracting intelligence..."):
                        st.session_state.ai_result = parse_with_ollama([prompt], task)
                
                # DISPLAY RESULTS

                try:
                    clean_json = st.session_state.ai_result.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)
                    
                    # Helper to prevent "NoneType" errors
                    def safe_int(val):
                        try:
                            if val is None: return 0
                            return int(val)
                        except (ValueError, TypeError):
                            return 0
                    
                    # 1. LEETCODE DISPLAY
                    if platform == "LeetCode":
                        st.markdown("### 🟡 LeetCode Status")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Rank / Tier", parsed.get("rank", "N/A"))
                        c2.metric("Problems Solved", parsed.get("problems_solved", 0))
                        
                        curr = safe_int(parsed.get("contest_rating"))
                        mx = safe_int(parsed.get("max_rating"))
                        c3.metric("Contest Rating", f"{curr}" if curr > 0 else "Unrated", 
                                 delta=f"{curr - mx} from Max" if (mx > 0 and curr > 0) else None)

                        c4, c5 = st.columns(2)
                        c4.metric("Badges Earned", parsed.get("badges", 0))
                        c5.metric("Top Language", parsed.get("top_language", "N/A"))

                        st.subheader("🛠️ Specialized Skills")
                        skills = parsed.get("top_skills", [])
                        if skills:
                            st.markdown(" ".join([f"`{s}`" for s in skills]))
                        else:
                            st.caption("No advanced skills found.")

                    # 2. CODECHEF DISPLAY
                    elif platform == "CodeChef":
                        st.markdown("### 🍳 CodeChef Status")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Global Rank", parsed.get("rank", "N/A"))
                        c2.metric("Problems Solved", parsed.get("problems_solved", 0))
                        
                        curr_str = str(parsed.get("contest_rating", "Unrated"))
                        mx = safe_int(parsed.get("max_rating"))
                        
                        # Extract number from string like "1600 (3★)" for delta calc
                        import re
                        match = re.search(r'\d+', curr_str)
                        curr_val = int(match.group()) if match else 0
                        
                        c3.metric("Current Rating", curr_str, 
                                 delta=f"{curr_val - mx} from Max" if (mx > 0 and curr_val > 0) else None)

                        c4, c5 = st.columns(2)
                        c4.metric("Badges", parsed.get("badges", 0))
                        c5.metric("Top Language", parsed.get("top_language", "N/A"))

                        st.divider()
                        st.subheader("🎓 Verified Skill Facts")
                        skills = parsed.get("top_skills", [])
                        if skills:
                            for skill in skills:
                                st.markdown(f"- ✅ **{skill}**")
                        else:
                            st.info("No verified skill assessments found.")

                    # 3. GENERIC / CODEFORCES
                    else:
                        st.markdown(f"### 📊 {platform} Analysis")
                        st.json(parsed)

                    # NEW: DISPLAY FULL RAW JSON (FOR DEBUGGING/AGENTS)
                    st.divider()
                    with st.expander("📂 View Full Agent JSON Response"):
                        st.json(parsed) # Display parsed JSON in expander

                except Exception as e:
                    # If JSON parsing fails completely, show raw text
                    st.warning("⚠️ Could not parse strict data. Here is the raw analysis:")
                    st.write(st.session_state.ai_result)

                with st.expander("🔍 View Raw Scraper Data"):
                    st.text(raw_text[:2000])
# TAB 2: PROJECT RATER (Keep your existing code)
with tab2:
    st.header("📂 Smart Project Rater")
    repo_url = st.text_input("Enter Repository URL", placeholder="https://github.com/username/project-name")
    
    if st.button("🚀 Auto-Analyze Project"):
        if repo_url:
            with st.spinner("1/3 Reading Documentation..."):
                details = get_project_details(repo_url)
                readme_text = details["readme_snippet"]
            
            with st.spinner("2/3 Finding Main Code Files..."):
                main_files = get_smart_main_files(repo_url)
                code_context = ""
                if main_files:
                    st.success(f"Detected: {', '.join(main_files.keys())}")
                    for name, link in main_files.items():
                        content = get_file_content(link)
                        code_context += f"\n\n--- FILE: {name} ---\n{content[:2000]}"
                else:
                    st.warning("No main file found. Analyzing README only.")

            with st.spinner("3/3 AI is grading the project..."):
                prompt = (
                    "You are a Senior Technical Architect. Evaluate this project.\n"
                    f"--- PROJECT INPUTS ---\n"
                    f"README Snippet:\n{readme_text[:3000]}\n\n"
                    f"CODE SAMPLES:\n{code_context}\n\n"
                    "--- REQUIRED OUTPUT FORMAT ---\n"
                    "Project Score: [0-10]\n"
                    "Complexity: [Low / Medium / High]\n"
                    "Code Quality: [Clean / Average / Spaghetti]\n"
                    "Verdict: [Hire / No Hire]\n"
                )
                result = parse_with_ollama([prompt], "Rate Project")
                st.markdown("### 🏆 AI Analysis Result")
                st.markdown(result)

# TAB 3: BATCH PROCESSOR (Keep your existing code)
with tab3:
    st.header("🚀 Bulk Candidate Evaluation")
    urls_input = st.text_area("Enter URLs (one per line):", height=150)
    
    if st.button("Analyze All Candidates"):
        if urls_input:
            urls = [line.strip() for line in urls_input.split('\n') if line.strip()]
            with st.spinner(f"Launching {len(urls)} parallel browsers..."):
                results = scrape_multiple_profiles(urls, max_workers=3)
            
            st.success("Scraping Complete!")
            
            comparison_data = []
            for username, stats in results.items():
                if "error" in stats: continue
                comparison_data.append({
                    "Candidate": username,
                    "Total Commits": stats.get('total_commits', 0),
                    "Consistency": stats.get('consistency_score', 'N/A'),
                    "Active Days": stats.get('active_days', 0),
                    "Max Gap": stats.get('max_gap', 0)
                })
            
            if comparison_data:
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)