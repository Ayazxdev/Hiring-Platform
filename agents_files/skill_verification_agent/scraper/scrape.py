import time
import re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    webdriver = None
    Options = None
    By = None
    WebDriverWait = None
    EC = None
from bs4 import BeautifulSoup

# SECTION 1: CORE UTILITIES & DRIVER SETUP

def setup_driver(headless=True):
    """
    Initializes the browser.
    Args:
        headless (bool): If False, opens a visible browser (needed for LinkedIn).
    """
    if not HAS_SELENIUM:
        print("⚠️ Selenium not installed. Skipping browser automation.")
        return None

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ Failed to initialize Chrome driver: {e}")
        return None

def identify_platform(url):
    """Router logic to identify the target website"""
    if "linkedin.com" in url: return "LinkedIn"
    if "github.com" in url: return "GitHub"
    if "leetcode.com" in url: return "LeetCode"
    if "codeforces.com" in url: return "Codeforces"
    if "codechef.com" in url: return "CodeChef"
    return "Generic"

# SECTION 2: THE UNIVERSAL ROUTER (New)

def scrape_dynamic_page(url, platform):
    """
    New Scraper for Non-GitHub sites (LinkedIn, LeetCode) that need scrolling.
    """
    # LinkedIn blocks headless browsers often, so we toggle it based on platform
    is_headless = False if platform == "LinkedIn" else True
    
    driver = setup_driver(headless=is_headless)
    if not driver:
        return {"error": "Selenium driver not available"}
    try:
        print(f"🕵️ Scraping {platform}: {url}")
        driver.get(url)
        time.sleep(3)

        # Scroll for lazy loading (Critical for LinkedIn/LeetCode)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Clean junk to save tokens
        for tag in soup(["script", "style", "nav", "footer", "svg", "noscript"]):
            tag.decompose()
            
        return {
            "platform": platform,
            "content": soup.get_text(separator="\n")[:20000], # Expanded context
            "raw_html": str(soup)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()

# SECTION 3: ORIGINAL GITHUB SCRAPER (Preserved)

def scrape_website(website):
    """
    Your ORIGINAL GitHub Scraper logic.
    Kept specifically for the GitHub Consistency & Contribution checks.
    """
    print(f"Launching scraper for: {website}")
    driver = setup_driver(headless=True)
    if not driver:
        return ""
    try:
        driver.get(website)
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        return driver.page_source
    finally:
        driver.quit()

def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    if body_content: return str(body_content)
    return ""

def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, "html.parser")
    for element in soup(["script", "style", "meta", "noscript", "svg", "img", "header", "footer"]):
        element.extract()
    cleaned_content = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in cleaned_content.splitlines() if line.strip())[:100000]

def split_dom_content(dom_content, max_length=6000):
    return [dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)]

# SECTION 4: GITHUB STATS & CONSISTENCY (Preserved)

def get_contribution_count(html_content):
    """Returns the text displayed on the GitHub header."""
    soup = BeautifulSoup(html_content, "html.parser")
    pattern = re.compile(r"([\d,]+)\s+contributions", re.IGNORECASE)
    
    target_tag = soup.find("h2", string=pattern)
    if target_tag:
        match = pattern.search(target_tag.get_text())
        if match: return match.group(0)
            
    fallback = soup.find(string=pattern)
    if fallback:
        match = pattern.search(fallback)
        if match: return match.group(0)
            
    return "Count not found"

def get_contribution_history(html_content):
    """
    Parses the graph to create a structured 'Activity Log'.
    Calculates monthly breakdowns and recent streaks.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    day_elements = soup.find_all(attrs={"data-date": True})
    active_dates = []
    monthly_counts = {}
    
    for day in day_elements:
        try:
            date_str = day["data-date"]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            if start_date <= date_obj <= end_date:
                month_key = date_obj.strftime("%Y-%m")
                tool_tip = day.get_text(strip=True)
                count = 0
                if "contribution" in tool_tip:
                    match = re.search(r"(\d+)\s+contribution", tool_tip)
                    if match: count = int(match.group(1))
                elif day.get("data-level") != "0":
                    count = 1
                
                if count > 0:
                    active_dates.append(date_obj)
                    monthly_counts[month_key] = monthly_counts.get(month_key, 0) + count
        except: continue

    active_dates.sort()
    
    if not active_dates:
        return {"error": "No activity found", "total_commits": 0}

    last_active = active_dates[-1]
    days_since_last = (end_date - last_active).days
    recent_threshold = end_date - timedelta(days=30)
    commits_last_30_days = sum(1 for d in active_dates if d >= recent_threshold)
    
    gaps = []
    for i in range(1, len(active_dates)):
        gaps.append((active_dates[i] - active_dates[i-1]).days)
    max_gap = max(gaps) if gaps else 0
    avg_gap = sum(gaps) / len(gaps) if gaps else 0

    return {
        "monthly_log": monthly_counts,
        "total_commits": sum(monthly_counts.values()),
        "days_since_last_commit": days_since_last,
        "commits_last_30_days": commits_last_30_days,
        "max_gap": max_gap,
        "avg_gap": round(avg_gap, 1),
        "active_days": len(active_dates),
        "period": f"{start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}",
        "gaps": gaps
    }

def get_total_lifetime_contributions(username):
    """Sum contributions from all years available in the sidebar."""
    driver = setup_driver()
    if not driver:
        # Return default 0 contributions if headless browser is unavailable
        return 0

    total_contributions = 0
    try:
        base_url = f"https://github.com/{username}"
        driver.get(base_url)
        time.sleep(2)
        
        links = driver.find_elements(By.TAG_NAME, "a")
        year_urls = set()
        for link in links:
            try:
                href = link.get_attribute("href")
                if href and f"/{username}" in href and "?from=" in href:
                    year_urls.add(href)
            except: continue
        
        if not year_urls:
            dropdown_items = driver.find_elements(By.CSS_SELECTOR, ".js-year-link")
            for item in dropdown_items:
                href = item.get_attribute("href")
                if href: year_urls.add(href)

        year_urls = sorted(list(year_urls), reverse=True)
        if not year_urls:
            text = get_contribution_count(driver.page_source)
            if "contributions" in text:
                return int(text.split()[0].replace(",", ""))
            return 0

        for url in year_urls:
            driver.get(url)
            time.sleep(1)
            count_text = get_contribution_count(driver.page_source)
            if "contributions" in count_text:
                num = int(count_text.split()[0].replace(",", ""))
                total_contributions += num
        return total_contributions
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        driver.quit()

def scrape_multiple_profiles(urls, max_workers=3):
    """Parallel processing for Batch Analysis"""
    results = {}
    print(f"Starting parallel scrape for {len(urls)} URLs...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(get_contribution_history, scrape_website(url)): url 
            for url in urls
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            username = url.strip("/").split("/")[-1]
            try:
                data = future.result()
                results[username] = data
                print(f"✅ Finished: {username}")
            except Exception as e:
                print(f"❌ Failed: {url} - {e}")
                results[username] = {"error": str(e)}
    return results

# SECTION 5: PROJECT & FILE ANALYSIS (Preserved)

def get_project_details(repo_url):
    """Scrapes README and metadata"""
    driver = setup_driver()
    if not driver:
        return {"url": repo_url, "languages": [], "readme_snippet": "Selenium not installed", "error": "No driver"}
    try:
        driver.get(repo_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        languages = [l.get_text(strip=True) for l in soup.find_all("span", class_="color-fg-default text-bold mr-1")]
        
        readme_text = ""
        readme_article = soup.find("article", class_="markdown-body")
        if readme_article:
            readme_text = readme_article.get_text(separator="\n").strip()[:5000]
            
        return {"url": repo_url, "languages": languages, "readme_snippet": readme_text}
    finally:
        driver.quit()

def get_repo_file_list(repo_url):
    """Scrapes file list from repo home"""
    driver = setup_driver()
    file_map = {}
    if not driver:
        # Fallback for no selenium - return empty or error
        return {}
    try:
        driver.get(repo_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        base_path = "/".join(repo_url.split("/")[-2:])
        
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if f"/{base_path}/blob/" in href and text:
                file_map[text] = f"https://github.com{href}"
        return file_map
    finally:
        driver.quit()

def get_file_content(file_url):
    """Reads raw code from a file"""
    driver = setup_driver()
    if not driver:
        return "Error: Selenium not installed."
    try:
        driver.get(file_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        text_area = soup.find("textarea", {"id": "read-only-cursor-text-area"})
        if text_area: return text_area.get_text()
        
        lines = soup.find_all("td", class_="blob-code")
        if lines: return "\n".join([l.get_text(strip=False) for l in lines])
            
        return "Error: Could not read file content."
    finally:
        driver.quit()

def get_smart_main_files(repo_url):
    """Filters for main entry points (e.g. main.py)"""
    all_files = get_repo_file_list(repo_url)
    
    # Priority 1: The "Truth" Files (Dependencies)
    DEPENDENCY_FILES = ["package.json", "requirements.txt", "go.mod", "pom.xml", "Gemfile", "composer.json"]
    # Priority 2: The "Logic" Files (Entry Points)
    ENTRY_FILES = ["main.py", "app.py", "index.js", "app.js", "server.js", "index.html", "main.go"]
    
    selected = {}
    
    # 1. Grab Dependency Files FIRST
    for fname, url in all_files.items():
        if fname in DEPENDENCY_FILES:
             selected[fname] = url

    # 2. Grab Main Logic Files (Limit to top 2 to save tokens)
    logic_count = 0
    for fname, url in all_files.items():
        if fname.lower() in ENTRY_FILES:
            selected[fname] = url
            logic_count += 1
            if logic_count >= 2: break
            
    # Fallback if no specific entry points found
    if not selected:
        for fname, url in all_files.items():
            if fname.endswith((".py", ".js", ".html")):
                selected[fname] = url
                if len(selected) >= 1: break
    return selected

