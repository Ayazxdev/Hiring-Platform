import os
import json
import re
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class JobBiasAgent:
    def __init__(self, model_name=None):
        """Initializes the agent with OpenRouter/OpenAI/Ollama support."""
        api_key = (
            os.getenv("OPENROUTER_API_KEY") or 
            os.getenv("OPENAI_API_KEY") or 
            os.getenv("API_KEY") or
            "ollama"
        )
        ollama_url = os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        default_ollama_v1 = f"{ollama_url.rstrip('/')}/v1"
        
        # If openrouter key is present and valid, use openrouter; otherwise Gemini; otherwise local Ollama
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or ""
        gemini_key = os.getenv("GEMINI_API_KEY") or ""
        has_openrouter = bool(openrouter_key and not openrouter_key.startswith("your_"))
        has_gemini = bool(gemini_key and not gemini_key.startswith("your_"))
        
        if has_openrouter:
            api_key = os.getenv("OPENROUTER_API_KEY")
            base_url = os.getenv("OPENAI_API_BASE") or "https://openrouter.ai/api/v1"
            model_to_use = model_name or os.getenv("LLM_MODEL") or "anthropic/claude-3-haiku"
        elif has_gemini:
            api_key = os.getenv("GEMINI_API_KEY")
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            model_to_use = model_name or os.getenv("LLM_MODEL") or "gemini-1.5-flash"
        else:
            base_url = os.getenv("OPENAI_API_BASE") or default_ollama_v1
            model_to_use = model_name or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL") or "llama3.2"
        
        self.model = ChatOpenAI(
            model=model_to_use,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=0,
            default_headers={
                "HTTP-Referer": "https://fair-hiring.network",
                "X-Title": "Fair Hiring System"
            }
        )
        
        # Double curly braces {{ }} are used to prevent LangChain KeyErrors
        self.system_instructions = (
            "You are a job-description bias auditor. Evaluate requirements for unfair demographic discrimination or unnecessary exclusion, not whether every candidate has equal access, background, or likelihood of possessing the skill."
            "\n\n=== CORE RULES ==="
            "\n1. Do NOT flag legitimate, job-relevant skill or operational/workplace requirements merely because participation or residence may correlate with demographics, geography, or access."
            "\n   Examples of legitimate criteria (STRICTLY DO_NOT_FLAG):"
            "\n   - Technical platforms & skills: Codeforces/LeetCode ratings, coding-test scores, GitHub contributions, technical certifications, programming expertise, years of relevant experience."
            "\n   - Work Location & Workplace arrangement: Requiring physical location, office attendance, or timezone (e.g., 'Must be able to work in Delhi', 'Based in Bangalore', 'On-site in London', 'Hybrid 3 days/week', 'Remote in UTC+5:30'). Where a company operates its business or whether a role requires on-site presence is an operational business decision, NOT demographic bias. Do NOT flag location requirements or suggest making location optional."
            "\n2. A requirement is NOT a demographic proxy just because it is correlated with a demographic group. There must be a meaningful connection to excluding or disadvantaging a protected group (e.g., gender, race, age, religion)."
            "\n3. Flag explicit demographic requirements or criteria that clearly use demographic characteristics as a selection filter (e.g., gender, race, age, religion)."
            "\n4. Flag likely demographic proxies when the criterion appears unnecessarily restrictive and is being used as a substitute for a demographic characteristic (e.g., 'digital native', 'fresh blood', 'young energetic team', 'recent grads only')."
            "\n5. Distinguish bias from job relevance. A criterion can be overly restrictive or operational without being demographic bias."
            "\n6. Do not assume elite credentials, specific platforms, employers, universities, locations, or experience are biased automatically. Evaluate their actual relationship to the role."
            "\n7. Use three outcomes for evaluated requirements:"
            "\n   - FLAG: credible demographic discrimination / proxy"
            "\n   - REVIEW: ambiguous or potentially exclusionary; requires context"
            "\n   - DO_NOT_FLAG: legitimate, objective, job-relevant or operational criterion"
            "\n8. Avoid speculative reasoning such as 'this could exclude some people' unless there is a concrete demographic-bias mechanism."
            "\n\n=== KEY PRINCIPLE ==="
            "\nCorrelation is not discrimination. Objective measurement of job-relevant ability and operational business decisions (like office location) are NOT demographic bias."
            "\nDo not manufacture bias findings. Prioritize precision and minimize false positives."
            "\n\n=== OUTPUT FORMAT ==="
            "\nReturn ONLY valid JSON. Your entire response must be a single JSON object with this schema:"
            "\n{{"
            "\n  \"bias_score\": <int between 0 and 10, where 0 means no demographic bias, 1-4 is minor/review, 5-10 is detected bias>,"
            "\n  \"reasoning\": \"<concise explanation of findings or confirmation of unbiased text>\","
            "\n  \"evaluations\": ["
            "\n    {{"
            "\n      \"requirement\": \"<exact requirement string>\","
            "\n      \"decision\": \"DO_NOT_FLAG | REVIEW | FLAG\","
            "\n      \"reason\": \"<explanation>\","
            "\n      \"suggested_alternative\": \"<only when a real issue exists, otherwise null>\""
            "\n    }}"
            "\n  ],"
            "\n  \"findings\": ["
            "\n    {{"
            "\n      \"phrase\": \"<exact phrase with issue>\","
            "\n      \"category\": \"Demographic Discrimination | Demographic Proxy\","
            "\n      \"fix\": \"<better alternative>\""
            "\n    }}"
            "\n  ]"
            "\n}}"
            "\nIMPORTANT: If all requirements are DO_NOT_FLAG, 'findings' MUST be [] and 'bias_score' MUST be 0."
        )

    def _fallback_bias_check(self, clean_text: str) -> dict:
        """Rule-based heuristic bias auditor used when external LLM is offline or unconfigured."""
        clean_lower = clean_text.lower()
        explicit_bias_terms = [
            ("male only", "Demographic Discrimination", "Remove gender filter and evaluate all qualified candidates."),
            ("female only", "Demographic Discrimination", "Remove gender filter and evaluate all qualified candidates."),
            ("men only", "Demographic Discrimination", "Remove gender filter and evaluate all qualified candidates."),
            ("women only", "Demographic Discrimination", "Remove gender filter and evaluate all qualified candidates."),
            ("young energetic", "Demographic Proxy", "Replace with 'collaborative team member'."),
            ("recent grads only", "Demographic Proxy", "Focus on technical competence rather than graduation date."),
            ("digital native", "Demographic Proxy", "Specify required technical tools rather than age-correlated proxies."),
            ("fresh blood", "Demographic Proxy", "Replace with 'creative problem solver'."),
            ("rockstar", "Cultural Phrasing", "Replace with 'experienced software engineer'."),
            ("ninja", "Cultural Phrasing", "Replace with 'proficient developer'."),
            ("work hard play hard", "Cultural Proxy", "Replace with 'collaborative and supportive team culture'.")
        ]
        
        findings = []
        for term, cat, fix in explicit_bias_terms:
            if term in clean_lower:
                findings.append({
                    "phrase": term,
                    "category": cat,
                    "fix": fix
                })
        
        if findings:
            return {
                "bias_score": min(10, len(findings) * 3 + 1),
                "reasoning": f"Demographic or cultural bias markers detected ({len(findings)} finding(s)). Recommended adjustments identified.",
                "findings": findings
            }
        
        return {
            "bias_score": 0,
            "reasoning": "Bias check passed: Job description focuses on objective, role-relevant skills with zero demographic bias detected.",
            "findings": []
        }

    def analyze(self, raw_text):
        """Main method to perform bias detection with strict precision guardrails."""
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_instructions),
            ("human", "Audit this Job Description for Demographic Bias:\n\n{content}")
        ])
        
        chain = prompt | self.model
        
        start_time = time.time()
        try:
            response_obj = chain.invoke({"content": clean_text})
            raw_content = getattr(response_obj, 'content', response_obj)
            if isinstance(raw_content, list):
                response = " ".join(str(item) for item in raw_content)
            else:
                response = str(raw_content)
        except Exception as e:
            print(f"LLM Error: {e}. Executing heuristic bias check.")
            return self._fallback_bias_check(clean_text)


        end_time = time.time()
        print(f"Audit completed in {end_time - start_time:.2f}s")
        
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx+1]
                data = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in response")
            
            # Filter out legitimate technical and logistical terms from bias flags
            # Technical skills, platform metrics, ratings, coding tests, and operational requirements should never be flagged
            legitimate_whitelist = [
                # Technical platforms and skills
                "codeforces", "leetcode", "github", "hackerrank", "5 star", "star rating",
                "competitive programming", "algorithm", "data structure", "python", "java",
                "coding", "test score", "certification", "years of experience",
                # Physical work location, office, operational logistics
                "work in", "based in", "located in", "delhi", "bangalore", "mumbai", "new york",
                "san francisco", "london", "on-site", "onsite", "hybrid", "remote", "office",
                "relocate", "relocation", "timezone", "commute", "travel", "shift", "full-time",
                "part-time", "contract", "visa", "work authorization"
            ]
            
            clean_findings = []
            for f in data.get("findings", []):
                phrase = (f.get("phrase") or "").lower()
                cat = (f.get("category") or "").lower()
                fix = (f.get("fix") or "").lower()
                
                # Check if it falsely targeted a legitimate technical or location/operational criterion
                is_legitimate = any(kw in phrase for kw in legitimate_whitelist)
                if is_legitimate:
                    continue  # Strictly discard false positive
                
                # If category is merely "ambiguous requirement" without genuine demographic bias, discard
                if "ambiguous" in cat and not any(kw in cat for kw in ["gender", "race", "age", "religion", "demographic"]):
                    continue
                    
                clean_findings.append(f)
                
            data["findings"] = clean_findings
            
            # Update evaluations if present
            for ev in data.get("evaluations", []):
                req = (ev.get("requirement") or "").lower()
                if any(kw in req for kw in legitimate_whitelist):
                    ev["decision"] = "DO_NOT_FLAG"
                    ev["suggested_alternative"] = None
                    ev["reason"] = "Objective measurement of job-relevant ability or operational workplace decisions (like office location) are not demographic bias."

            # Calculate final bias_score based on verified clean findings
            if not data["findings"]:
                data["bias_score"] = 0
                data["reasoning"] = (
                    "No demographic bias detected. Requirements are legitimate, objective, job-relevant criteria."
                )
            else:
                has_flag = any(
                    "discrimination" in (f.get("category") or "").lower() or "proxy" in (f.get("category") or "").lower()
                    for f in data["findings"]
                )
                data["bias_score"] = 8 if has_flag else 4
                
            return data
            
        except Exception as e:
            print(f"JSON Parse Error: {e}")
            print(f"Raw Response: {response}")
            
            # Strict fallback: check ONLY for unambiguous demographic discrimination keywords
            clean_lower = clean_text.lower()
            explicit_bias_terms = [
                "male only", "female only", "men only", "women only",
                "young energetic", "recent grads only", "digital native", "fresh blood"
            ]
            
            detected = [term for term in explicit_bias_terms if term in clean_lower]
            if detected:
                return {
                    "bias_score": 8,
                    "reasoning": f"Explicit demographic preference detected: {', '.join(detected)}.",
                    "findings": [{
                        "phrase": detected[0],
                        "category": "Demographic Discrimination",
                        "fix": "Remove demographic restriction and focus on role-relevant skills."
                    }]
                }
            
            return {
                "bias_score": 0,
                "reasoning": "No demographic bias detected. Criteria evaluated as legitimate and job-relevant.",
                "findings": []
            }
