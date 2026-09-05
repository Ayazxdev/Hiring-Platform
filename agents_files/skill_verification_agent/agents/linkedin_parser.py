"""
LinkedIn PDF Parser (Redesigned)

Extracts ONLY structured facts from user-provided LinkedIn PDFs.
NO scoring. NO verification. NO judgment.

Outputs:
- experience.timeline (company, role, dates)
- experience.total_years
- experience.consistency (stable/frequent_switches)
- skills.claimed
- identity (name, headline, location)

Source: linkedin_pdf
"""
import logging
import os
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LinkedInPDFParser:
    """
    Parse LinkedIn PDF exports and extract structured facts.
    
    IMPORTANT: This parser extracts CLAIMS only - no verification.
    Verification happens in the main agent pipeline.
    """
    
    def __init__(self, llm=None):
        """
        Initialize parser.
        
        Args:
            llm: Optional LLM for better structuring (Ollama/OpenAI)
        """
        self.llm = llm
    
    
    # Backward compatibility alias
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Alias for parse() - backward compatibility"""
        return self.parse(pdf_path)
    
    def parse(self, pdf_path: str) -> Dict:
        """
        Parse LinkedIn PDF and return structured facts.
        
        Args:
            pdf_path: Path to the LinkedIn PDF file
            
        Returns:
            Dict with experience, skills, identity - FACTS ONLY
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF not found: {pdf_path}")
            return self._empty_result("file_not_found")
        
        try:
            import pypdf
            
            # 1. Extract raw text from PDF
            text = self._extract_text(pdf_path)
            logger.info(f"Extracted {len(text)} chars from LinkedIn PDF")
            
            if len(text) < 50:
                return self._empty_result("empty_pdf")
            
            # 2. Structure the data
            if self.llm:
                return self._parse_with_llm(text)
            else:
                return self._parse_with_regex(text)
                
        except ImportError:
            logger.error("pypdf not installed. Run: pip install pypdf")
            return self._empty_result("pypdf_missing")
        except Exception as e:
            logger.error(f"Failed to parse LinkedIn PDF: {e}")
            return self._empty_result("parse_error")
    
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF"""
        import pypdf
        
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text.strip()
    
    
    def _parse_with_llm(self, text: str) -> Dict:
        """
        Use LLM to extract structured facts from LinkedIn PDF text.
        
        Returns ONLY facts - no scoring, no judgment.
        """
        prompt = f"""
Extract structured facts and signals from this LinkedIn Profile PDF text for a "Clean & Honest" v2 verification.

### PHILOSOPHY:
- LinkedIn is SUPPLEMENTARY, not punitive.
- Do NOT penalize early-career candidates for minimal profiles.
- Focus on "Learning Velocity" and "Applied Engineering" signals.
- NO years-inflation or seniority claims.

### RULES:
1. "suspicious_patterns" must be FALSE unless there is clear evidence of gross deception (e.g., claiming 10 years experience as a student). Early-career minimal profiles are NOT suspicious.
2. "resume_consistent" must be TRUE if the domain (e.g., CV/UAV/AI) matches the headline and role, even if the phrasing differs slightly.
3. "profile_complete" must be TRUE if Name, Headline, and at least one Experience or Education entry is present.
4. "confidence_score" should range from 0.55 to 0.65 for credible early-career profiles with real project evidence.

TEXT:
{text[:6000]}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "identity": {{
    "name": "Full Name",
    "headline": "Professional headline",
    "location": "City, Country"
  }},
  "profile_signals": {{
    "headline_present": true,
    "summary_present": true,
    "location_present": true,
    "profile_complete": true
  }},
  "experience_signals": {{
    "total_roles_listed": 1,
    "role_types": ["applied_engineering"],
    "tenure_consistency": "early-career",
    "gaps_detected": false
  }},
  "skills_signals": {{
    "skills_listed": ["Python", "YOLOv8"],
    "endorsement_count": {{}}
  }},
  "activity_signals": {{
    "posts_present": false,
    "technical_posts_detected": false,
    "recent_activity_days": null
  }},
  "credibility_flags": {{
    "profile_complete": true,
    "suspicious_patterns": false,
    "buzzword_heavy": false,
    "resume_consistent": true
  }},
  "confidence_score": 0.6,
  "experience_timeline": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "start": "YYYY-MM",
      "end": "present"
    }}
  ],
  "education": [
    {{
      "school": "Name",
      "degree": "Degree",
      "year": "YYYY"
    }}
  ]
}}
"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Handle both Ollama (string) and ChatOpenAI (object with .content)
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Clean markdown wrappers if present
            content = self._clean_json_response(content)
            
            import json
            data = json.loads(content)
            
            # Build structured output
            return self._build_result(data)
            
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}. Using regex fallback.")
            return self._parse_with_regex(text)
    
    
    def _parse_with_regex(self, text: str) -> Dict:
        """
        Fallback regex-based parsing for LinkedIn PDFs.
        
        LinkedIn PDFs have specific patterns we can match.
        """
        experience_timeline = self._extract_experience_regex(text)
        skills = self._extract_skills_regex(text)
        identity = self._extract_identity_regex(text)
        
        # Build v2 skeleton for fallback
        result = {
            "source": "linkedin_pdf",
            "parse_method": "regex_fallback",
            "identity": identity,
            "profile_signals": {
                "headline_present": bool(identity.get("headline")),
                "summary_present": "summary" in text.lower(),
                "location_present": bool(identity.get("location")),
                "profile_complete": True  # Non-punitive default
            },
            "experience_signals": {
                "total_roles_listed": len(experience_timeline),
                "role_types": ["early-career"],
                "tenure_consistency": self._determine_consistency(experience_timeline),
                "gaps_detected": False
            },
            "skills_signals": {
                "skills_listed": skills,
                "endorsement_count": {}
            },
            "activity_signals": {
                "posts_present": False,
                "technical_posts_detected": False,
                "recent_activity_days": None
            },
            "credibility_flags": {
                "profile_complete": True,  # Non-punitive default
                "suspicious_patterns": False,  # Non-punitive default
                "buzzword_heavy": False,
                "resume_consistent": True  # Assume honest first
            },
            "confidence_score": 0.55,  # Standard baseline for early career
            "experience": self._build_experience_output(experience_timeline),
            "skills": {"claimed": skills},
            "education": [],
            "raw_text_sample": text[:500]
        }
        
        return result


    def _extract_experience_regex(self, text: str) -> List[Dict]:
        """Attempt to extract experience timeline using regex fallback"""
        # Look for "Experience" section
        # More flexible pattern to find experience section block
        exp_match = re.search(r"Experience\n(.*?)(?=\nEducation|\nSkills|\nCertifications|\n#|$)", text, re.DOTALL | re.IGNORECASE)
        if not exp_match:
            return []
            
        exp_text = exp_match.group(1).strip()
        # Split by blocks (sometimes companies are separated by double newlines or horizontal lines)
        blocks = re.split(r"\n\s*\n|(?=^.{1,100}\n.{1,100}\n[A-Z][a-z]+ \d{4})", exp_text, flags=re.MULTILINE)
        
        timeline = []
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines: continue
            
            # Simple heuristic for LinkedIn PDF structure:
            # Line 0: Company
            # Line 1: Role
            # Line 2: Dates (e.g. November 2025 - Present)
            if len(lines) >= 3:
                # Basic check if line 2 looks like a date range
                date_line = lines[2]
                if any(m in date_line.lower() for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "present"]):
                    company = lines[0]
                    role = lines[1]
                    
                    # Split dates (Handle normal dashes and non-breaking space dashes)
                    date_parts = re.split(r" [\u2013\u2014\-\u00a0]+\ ", date_line) # Added \u00a0
                    if len(date_parts) < 2:
                        # Try split by just the dash if spaces are missing
                        date_parts = re.split(r"[\u2013\u2014\-\u00a0]", date_line)
                        
                    start = date_parts[0].strip() if len(date_parts) > 0 else ""
                    end = date_parts[1].strip() if len(date_parts) > 1 else ""
                    
                    # Clean end date (remove durations like "(3 months)")
                    end = re.split(r" \(", end)[0].strip()
                    
                    # If end contains "Present" or similar, normalize it
                    if re.search(r"present|current|now", end.lower()):
                        end = "present"
                    
                    timeline.append({
                        "company": company,
                        "role": role,
                        "start": self._normalize_date(start),
                        "end": self._normalize_date(end),
                        "employment_type": "Unknown",
                        "source": "linkedin_pdf"
                    })
        
        return timeline
    
    
    def _extract_identity_regex(self, text: str) -> Dict:
        """Extract name and headline from text"""
        lines = text.split("\n")
        
        name = lines[0].strip() if lines else "Unknown"
        headline = lines[1].strip() if len(lines) > 1 else ""
        
        # Try to find location
        location = ""
        for line in lines[:10]:
            if any(loc in line.lower() for loc in ["india", "usa", "uk", "canada", "delhi", "mumbai", "bangalore"]):
                location = line.strip()
                break
        
        return {
            "name": name,
            "headline": headline,
            "location": location
        }
    
    
    def _extract_skills_regex(self, text: str) -> List[str]:
        """Extract skills mentioned in text"""
        # Common tech skills to look for
        skill_patterns = [
            r"Python", r"JavaScript", r"TypeScript", r"Java", r"C\+\+", r"Go",
            r"React", r"Node\.js", r"Vue", r"Angular", r"Django", r"Flask",
            r"AWS", r"Azure", r"GCP", r"Docker", r"Kubernetes",
            r"Machine Learning", r"Deep Learning", r"TensorFlow", r"PyTorch",
            r"YOLO", r"OpenCV", r"Computer Vision", r"NLP",
            r"PX4", r"MAVSDK", r"ROS", r"Drone", r"UAV",
            r"SQL", r"MongoDB", r"PostgreSQL", r"MySQL",
            r"Git", r"CI/CD", r"Linux"
        ]
        
        found_skills = []
        for pattern in skill_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Normalize case
                found_skills.append(pattern.replace(r"\+\+", "++").replace(r"\.", "."))
        
        return list(set(found_skills))
    
    
    def _build_result(self, data: Dict) -> Dict:
        """
        Build final structured output (v2 schema) from LLM response.
        """
        experience_list = data.get("experience_timeline") or data.get("experience", [])
        
        # Normalize timeline
        timeline = []
        for exp in experience_list:
            timeline.append({
                "company": exp.get("company", "Unknown"),
                "role": exp.get("role", "Unknown"),
                "start": self._normalize_date(exp.get("start", "")),
                "end": self._normalize_date(exp.get("end", "")),
                "employment_type": exp.get("employment_type", "Unknown"),
                "source": "linkedin_pdf"
            })
        
        # Calculate total years for internal reference
        total_years = self._calculate_total_years(timeline)
        
        return {
            "source": "linkedin_pdf",
            "parse_method": "llm",
            "identity": data.get("identity", {}),
            "profile_signals": data.get("profile_signals", {
                "profile_complete": True # Default to complete
            }),
            "experience_signals": data.get("experience_signals", {}),
            "skills_signals": data.get("skills_signals", {
                "skills_listed": data.get("skills", []),
                "endorsement_count": {}
            }),
            "activity_signals": data.get("activity_signals", {}),
            "credibility_flags": data.get("credibility_flags", {
                "profile_complete": True,
                "suspicious_patterns": False,
                "resume_consistent": True
            }),
            "confidence_score": max(0.55, min(0.65, data.get("confidence_score", 0.6))), # Enforce range
            "experience": {
                "total_years": round(total_years, 1),
                "consistency": data.get("experience_signals", {}).get("tenure_consistency", "stable"),
                "timeline": timeline
            },
            "education": data.get("education", [])
        }
    
    
    def _build_experience_output(self, timeline: List[Dict]) -> Dict:
        """Build experience output structure"""
        total_years = self._calculate_total_years(timeline)
        consistency = self._determine_consistency(timeline)
        
        return {
            "total_years": round(total_years, 1),
            "consistency": consistency,
            "timeline": timeline
        }
    
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date to YYYY-MM format.
        
        Handles:
        - "November 2025" -> "2025-11"
        - "2025-11" -> "2025-11"
        - "Present" -> "present"
        - "2025" -> "2025-01"
        """
        if not date_str:
            return ""
        
        # Normalize case and strip
        date_str = date_str.strip().lower().replace("\u00a0", " ")
        
        # Handle "present"
        if any(p in date_str for p in ["present", "current", "now"]):
            return "present"
        
        # Already in YYYY-MM format
        if re.match(r"^\d{4}-\d{2}$", date_str):
            return date_str
        
        # Handle "Month YYYY" format
        month_map = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "jun": "06", "jul": "07", "aug": "08", "sep": "09",
            "oct": "10", "nov": "11", "dec": "12"
        }
        
        parts = date_str.split()
        if len(parts) == 2:
            month_str = parts[0].lower()
            year_str = parts[1]
            if month_str in month_map and year_str.isdigit():
                return f"{year_str}-{month_map[month_str]}"
        
        # Handle just year
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01"
        
        return date_str
    
    
    def _calculate_total_years(self, timeline: List[Dict]) -> float:
        """Calculate total years of experience from timeline"""
        total_months = 0
        now = datetime.now()
        
        for exp in timeline:
            start = exp.get("start", "")
            end = exp.get("end", "")
            
            if not start:
                continue
            
            try:
                # Parse start
                if "-" in start:
                    start_year, start_month = map(int, start.split("-"))
                else:
                    continue
                
                # Parse end
                if end == "present":
                    end_year = now.year
                    end_month = now.month
                elif "-" in end:
                    end_year, end_month = map(int, end.split("-"))
                else:
                    continue
                
                months = (end_year - start_year) * 12 + (end_month - start_month)
                total_months += max(1, months)
                
            except (ValueError, TypeError):
                continue
        
        return total_months / 12
    
    
    def _determine_consistency(self, timeline: List[Dict]) -> str:
        """
        Determine career consistency from timeline.
        
        Returns: "stable" | "moderate" | "frequent_switches"
        """
        if len(timeline) <= 1:
            return "stable"
        elif len(timeline) <= 3:
            return "moderate"
        else:
            return "frequent_switches"
    
    
    def _clean_json_response(self, content: str) -> str:
        """Remove markdown code fences from LLM response"""
        content = content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
        
        return content.strip()
    
    
    def _empty_result(self, error_reason: str) -> Dict:
        """Return empty result structure with error"""
        return {
            "source": "linkedin_pdf",
            "error": error_reason,
            "identity": {},
            "experience": {
                "total_years": 0,
                "consistency": "unknown",
                "timeline": []
            },
            "skills": {
                "claimed": []
            },
            "education": []
        }


# Convenience function
def parse_linkedin_pdf(pdf_path: str, llm=None) -> Dict:
    """Quick function to parse a LinkedIn PDF"""
    parser = LinkedInPDFParser(llm=llm)
    return parser.parse(pdf_path)


if __name__ == "__main__":
    import sys
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse LinkedIn PDF")
    parser.add_argument("pdf_path", help="Path to LinkedIn PDF")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON without formatting")
    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    json_only = args.json_only
    
    # Try to load Ollama for better parsing
    llm = None
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model="qwen2.5:7b", temperature=0)
        if not json_only:
            print("✅ Using Ollama for parsing")
    except:
        if not json_only:
            print("⚠️ Ollama not available, using regex fallback")
    
    result = parse_linkedin_pdf(pdf_path, llm=llm)
    
    # Output JSON
    print(json.dumps(result, indent=2, default=str))
    
    if not json_only:
        print("\n✅ LinkedIn extraction complete")
