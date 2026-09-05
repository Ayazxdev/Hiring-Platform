
import json
from typing import Dict, List, Set

class MatchNormalizer:
    """
    Normalizes candidate data from various agent outputs (SkillAgent, GitHubAgent, etc.)
    into a flat, matchable schema for the Matching Engine v2.
    """
    
    @staticmethod
    def _normalize_tech_name(name: str) -> str:
        """Handles common tech aliases for better matching."""
        aliases = {
            "react.js": "react",
            "node.js": "node",
            "vue.js": "vue",
            "postgresql": "postgres",
            "mongodb": "mongo",
            # UAV / CV aliases
            "gazebo sitl": "gazebo",
            "gazebo_sitl": "gazebo",
            "mavsdk": "mavsdk",
            "mavlink": "mavlink",
            "yolov8": "yolov8",
            "yolov9": "yolov9",
            "arducopter": "arducopter",
            "arduplane": "arduplane",
            "ardu pilot": "ardupilot",
            "ardupilot": "ardupilot",
            "ardu_pilot": "ardupilot",
            "fastapi": "fastapi",
            "fast api": "fastapi",
            "opencv": "opencv",
            "open cv": "opencv",
            "px4 autopilot": "px4",
            "px 4": "px4",
            "bytetrack": "bytetrack",
            "deepsort": "deepsort",
            "deep sort": "deepsort",
        }
        name = name.lower().strip()
        return aliases.get(name, name)

    @staticmethod
    def normalize_candidate(credential: Dict) -> Dict:
        """
        Process the complex 'SkillAgent' output into a normalized form.
        """
        verified_skills = set()
        
        # 1. Flatten skills from the 'skills' list (resume extraction)
        skills_raw = credential.get("skills", [])
        for item in skills_raw:
            skill_text = ""
            if isinstance(item, dict):
                # Handle nested skill dictionaries like {"skill": {"name": "Python", ...}}
                skill_val = item.get("skill")
                if isinstance(skill_val, dict):
                    skill_text = skill_val.get("name", "")
                else:
                    skill_text = skill_val or ""
            elif isinstance(item, str):
                skill_text = item
            
            if skill_text:
                # Basic parsing of comma-separated strings
                parts = [p.strip() for p in str(skill_text).replace(":", ",").split(",")]
                for p in parts:
                    if p: 
                        verified_skills.add(MatchNormalizer._normalize_tech_name(p))

        # 1b. Also check structured 'verified_skills' if present (v2 format)
        v_dict = credential.get("verified_skills")
        if isinstance(v_dict, dict):
            for tier in v_dict.values():
                if isinstance(tier, list):
                    for s_item in tier:
                        s_name = ""
                        if isinstance(s_item, dict):
                            s_name = s_item.get("name", "")
                        elif isinstance(s_item, str):
                            s_name = s_item
                        if s_name:
                            verified_skills.add(MatchNormalizer._normalize_tech_name(s_name))

        # 2. Extract technical signals from 'experience' claims (all strengths)
        experience = credential.get("experience", [])
        for exp in experience:
            for claim in exp.get("claims", []):
                # Accept all evidence strengths — weak evidence still counts as partial signal
                techs = claim.get("technology", [])
                for t in techs:
                    verified_skills.add(MatchNormalizer._normalize_tech_name(t))

        # 2b. Extract from projects if present (ats evidence layer)
        projects = credential.get("projects", [])
        for proj in projects:
            for claim in proj.get("claims", []):
                for t in claim.get("technologies", []):
                    verified_skills.add(MatchNormalizer._normalize_tech_name(t))

        # 3. Extract GitHub signals
        # Use passed score if available, else derive
        github_score = credential.get("github_score", 0.0)
        github_signals = credential.get("github_signals", [])
        
        if not github_score and "github_present" in credential.get("identity", {}).get("public_links", []):
            github_score = 0.8  # Default for verified users
            github_signals = ["Project Ownership", "Commit Consistency", "Code Quality"]

        # 4. Learning Velocity
        learning_velocity = credential.get("learning_velocity")
        if learning_velocity is None:
            learning_velocity = 0.5  # Default baseline
            if any(exp.get("timeframe", "").endswith("Present") for exp in experience):
                learning_velocity += 0.3  # Active learner boost

        # 5. Hackathon / problem-solving signal
        has_hackathon = any(
            "hackathon" in s.lower() for s in credential.get("achievements", [])
        ) or "hackathon" in str(credential).lower()

        return {
            "verified_skills": list(verified_skills),
            "frameworks": list(verified_skills),
            "tools": list(verified_skills),
            "github_score": float(github_score),
            "github_signals": github_signals,
            "cp_activity": credential.get("cp_activity", False),
            "learning_velocity": min(1.0, float(learning_velocity)),
            "experience": experience,
            "has_hackathon": has_hackathon,
            "identity": credential.get("identity", {})
        }

    @staticmethod
    def normalize_job(jd: Dict) -> Dict:
        """
        Ensures JD v3 fields are ready for the matcher with normalized names.
        Handles both the legacy frontend_frameworks/backend_frameworks keys AND
        the newer 'frameworks', 'libraries_and_tools', 'domain_specific_skills' keys.
        """
        def norm_list(l):
            return [MatchNormalizer._normalize_tech_name(s) for s in (l or [])]

        # Collapse all framework-like fields into one unified list
        all_frameworks = (
            jd.get("frameworks", []) +
            jd.get("frontend_frameworks", []) +
            jd.get("backend_frameworks", [])
        )

        # Collapse tools: libraries_and_tools, developer_tools, domain_specific_skills
        all_tools = (
            jd.get("libraries_and_tools", []) +
            jd.get("developer_tools", []) +
            jd.get("domain_specific_skills", []) +
            jd.get("concepts", [])
        )

        # Infrastructure: explicit infra + kubernetes/docker type fields
        all_infra = (
            jd.get("infrastructure", []) +
            jd.get("infrastructure_concepts", []) +
            jd.get("backend_concepts", [])
        )

        return {
            "strict_requirements": norm_list(jd.get("strict_requirements", [])),
            "web_fundamentals": norm_list(jd.get("web_fundamentals", [])),
            "languages": norm_list(jd.get("languages", [])),
            "frontend_frameworks": norm_list(all_frameworks),
            "backend_frameworks": norm_list(all_frameworks),   # same set, matcher deduplicates via sets
            "infrastructure_concepts": norm_list(all_infra),
            "backend_concepts": norm_list(all_infra),
            "developer_tools": norm_list(all_tools),
            "soft_requirements": norm_list(jd.get("soft_requirements", [])),
            "problem_solving": jd.get("problem_solving", {"required": False, "signals": []}),
            "matching_philosophy": jd.get("matching_philosophy", {"learning_velocity_weight": 0.2})
        }
