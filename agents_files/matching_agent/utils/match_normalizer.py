
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
            # Programming languages
            "cpp": "c++",
            "c plus plus": "c++",
            "c/c++": "c++",
            "c/c++ ": "c++",
            "golang": "go",
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
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
            # Core CS & Architecture
            "dsa": "data structures & algorithms",
            "data structures": "data structures & algorithms",
            "algorithms": "data structures & algorithms",
            "data structures and algorithms": "data structures & algorithms",
            "ds & algo": "data structures & algorithms",
            "dbms": "dbms",
            "database management": "dbms",
            "database management system": "dbms",
            "database management systems": "dbms",
            "databases": "databases",
            "database": "databases",
            "relational databases": "databases",
            "nosql databases": "databases",
            "os": "operating systems",
            "operating system": "operating systems",
            "operating systems": "operating systems",
            "oop": "object-oriented programming",
            "object oriented programming": "object-oriented programming",
            "object-oriented programming": "object-oriented programming",
            "rest": "rest apis",
            "rest api": "rest apis",
            "restful": "rest apis",
            "restful api": "rest apis",
            "restful apis": "rest apis",
            "rest apis": "rest apis",
            "apis": "rest apis",
            "api": "rest apis",
            "async": "asynchronous programming",
            "asynchronous": "asynchronous programming",
            "async programming": "asynchronous programming",
            "asyncio": "asynchronous programming",
            "asynchronous programming": "asynchronous programming",
            "concurrency": "concurrent programming",
            "concurrent": "concurrent programming",
            "multithreading": "concurrent programming",
            "parallel programming": "concurrent programming",
            "concurrent programming": "concurrent programming",
            "ci/cd": "ci/cd",
            "ci / cd": "ci/cd",
            "cicd": "ci/cd",
            "continuous integration": "ci/cd",
            "continuous deployment": "ci/cd",
            "github actions": "ci/cd",
            "gitlab ci": "ci/cd",
            "git": "git",
            "github": "git",
            "gitlab": "git",
        }
        name = name.lower().strip()
        return aliases.get(name, name)

    @staticmethod
    def normalize_candidate(credential: Dict) -> Dict:
        """
        Process the complex 'SkillAgent' output into a normalized form.
        """
        verified_skills = set()
        
        # Helper to safely add normalized name
        def add_skill_str(raw: str):
            if not raw:
                return
            cleaned = str(raw).replace(":", ",").strip()
            for part in cleaned.split(","):
                norm = MatchNormalizer._normalize_tech_name(part.strip())
                if norm:
                    verified_skills.add(norm)

        # 1. Flatten skills from the 'skills' list (resume extraction)
        skills_raw = credential.get("skills", [])
        for item in skills_raw:
            if isinstance(item, dict):
                skill_val = item.get("skill")
                if isinstance(skill_val, dict):
                    add_skill_str(skill_val.get("name", ""))
                elif isinstance(skill_val, str):
                    add_skill_str(skill_val)
                else:
                    add_skill_str(item.get("name", ""))
            elif isinstance(item, str):
                add_skill_str(item)

        # 1b. Also check structured 'verified_skills' if present (v2 format)
        v_dict = credential.get("verified_skills")
        if isinstance(v_dict, dict):
            for tier in v_dict.values():
                if isinstance(tier, list):
                    for s_item in tier:
                        if isinstance(s_item, dict):
                            add_skill_str(s_item.get("name", "") or s_item.get("skill", ""))
                        elif isinstance(s_item, str):
                            add_skill_str(s_item)
        elif isinstance(v_dict, list):
            for s_item in v_dict:
                if isinstance(s_item, dict):
                    add_skill_str(s_item.get("name", "") or s_item.get("skill", ""))
                elif isinstance(s_item, str):
                    add_skill_str(s_item)

        # 2. Extract technical signals from 'experience' claims (all strengths)
        experience = credential.get("experience", [])
        for exp in experience:
            for claim in exp.get("claims", []):
                techs = claim.get("technology", [])
                for t in techs:
                    add_skill_str(t)

        # 2b. Extract from projects if present (ats evidence layer)
        projects = credential.get("projects", [])
        for proj in projects:
            for claim in proj.get("claims", []):
                for t in claim.get("technologies", []):
                    add_skill_str(t)

        # 3. Canonical Umbrella Inflections
        # If candidate has databases, give credit for databases and dbms
        db_indicators = {"postgres", "postgresql", "mysql", "mongo", "mongodb", "sql", "sqlite", "redis", "dbms"}
        if any(d in verified_skills for d in db_indicators):
            verified_skills.add("databases")
            verified_skills.add("dbms")

        # If candidate has web backends, give credit for REST APIs
        api_indicators = {"fastapi", "node", "express", "django", "flask", "grpc", "rest apis", "rest"}
        if any(a in verified_skills for a in api_indicators):
            verified_skills.add("rest apis")

        # If candidate has asynchronous libraries / runtimes
        async_indicators = {"fastapi", "tokio", "axum", "asyncio", "asynchronous programming"}
        if any(a in verified_skills for a in async_indicators):
            verified_skills.add("asynchronous programming")

        # If candidate has concurrency or Tokio JoinSet / multithreading
        concurrent_indicators = {"tokio", "axum", "multithreading", "concurrent programming", "concurrency"}
        if any(c in verified_skills for c in concurrent_indicators):
            verified_skills.add("concurrent programming")

        # If candidate has C++ or CPP
        if "c++" in verified_skills or "cpp" in verified_skills:
            verified_skills.add("c++")

        # If candidate has OS or Operating Systems
        if "os" in verified_skills or "operating systems" in verified_skills:
            verified_skills.add("operating systems")
            verified_skills.add("os")

        # If candidate has OOP or Object-Oriented Programming or known OOP languages
        oop_indicators = {"java", "c++", "cpp", "python", "c#", "oop", "object-oriented programming"}
        if any(o in verified_skills for o in oop_indicators):
            verified_skills.add("object-oriented programming")
            verified_skills.add("oop")

        # If candidate has DSA or Data Structures
        if "data structures & algorithms" in verified_skills or "dsa" in verified_skills or "algorithms" in verified_skills:
            verified_skills.add("data structures & algorithms")

        # If candidate has Git or GitHub
        if "git" in verified_skills or "github" in verified_skills or "gitlab" in verified_skills:
            verified_skills.add("git")

        # If candidate has Vector Search or FAISS
        if "faiss" in verified_skills or "vector search" in verified_skills:
            verified_skills.add("vector search")

        # If candidate has Distributed Systems or gRPC / Microservices / Tokio
        dist_indicators = {"grpc", "distributed systems", "distributed platforms", "microservices"}
        if any(d in verified_skills for d in dist_indicators):
            verified_skills.add("distributed systems")

        # If candidate has MCP or NLP or LLMs
        llm_indicators = {"mcp", "llm", "llms", "nlp", "transformers", "langchain"}
        if any(l in verified_skills for l in llm_indicators):
            verified_skills.add("llms")

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
            "experience_years": float(credential.get("experience_years") or 0.0),
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

        norm_strict = norm_list(jd.get("strict_requirements", []))

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

        all_fw_norm = norm_list(all_frameworks)
        all_infra_norm = norm_list(all_infra)
        all_tools_norm = norm_list(all_tools)

        # If categories were empty (e.g. from keyword fallback), populate from strict_requirements
        fw_keywords = {"react", "next.js", "node", "fastapi", "pytorch", "express", "vue", "angular", "django", "flask", "spring", "laravel"}
        infra_keywords = {"docker", "ci/cd", "postgres", "mongo", "databases", "dbms", "kubernetes", "aws", "gcp", "azure", "redis", "linux"}
        tool_keywords = {"git", "grpc", "rest apis", "rest", "mcp", "onnx", "vector search", "docker compose", "github actions", "gitlab ci"}

        if not all_fw_norm:
            all_fw_norm = [s for s in norm_strict if s in fw_keywords]
        if not all_infra_norm:
            all_infra_norm = [s for s in norm_strict if s in infra_keywords]
        if not all_tools_norm:
            all_tools_norm = [s for s in norm_strict if s in tool_keywords]

        return {
            "strict_requirements": norm_strict,
            "web_fundamentals": norm_list(jd.get("web_fundamentals", [])),
            "languages": norm_list(jd.get("languages", [])),
            "frontend_frameworks": all_fw_norm,
            "backend_frameworks": all_fw_norm,
            "infrastructure_concepts": all_infra_norm,
            "backend_concepts": all_infra_norm,
            "developer_tools": all_tools_norm,
            "soft_requirements": norm_list(jd.get("soft_requirements", [])),
            "problem_solving": jd.get("problem_solving", {"required": False, "signals": []}),
            "matching_philosophy": jd.get("matching_philosophy", {"learning_velocity_weight": 0.2})
        }
