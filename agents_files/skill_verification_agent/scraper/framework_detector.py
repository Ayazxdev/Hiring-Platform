"""
Framework Detector Module

Uses GitHub Linguist data + import scanning to detect frameworks/libraries
from actual code, not just metadata.

This module answers: "Is this skill ACTUALLY USED in code?"

Architecture:
1. Language Detection: File extension → Language (via GitHub Linguist)
2. Import Scanning: First 20 lines → Import patterns
3. Framework Mapping: Imports → Frameworks (YOLOv8, React, PX4, etc.)
"""
import re
import yaml
import json
import os
from typing import Dict, List, Set, Optional
from pathlib import Path

# Get the knowledge directory path
KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

# Load GitHub Linguist languages
def load_languages() -> Dict:
    """Load GitHub Linguist languages.yml"""
    with open(KNOWLEDGE_DIR / "languages.yml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Build extension to language mapping
LANGUAGES = load_languages()
EXTENSION_TO_LANGUAGE = {}

for lang_name, meta in LANGUAGES.items():
    if isinstance(meta, dict) and "extensions" in meta:
        for ext in meta["extensions"]:
            EXTENSION_TO_LANGUAGE[ext.lower()] = lang_name

# Import patterns per language
IMPORT_PATTERNS = {
    "Python": [
        r"^import\s+([\w.]+)",
        r"^from\s+([\w.]+)\s+import"
    ],
    "JavaScript": [
        r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
        r"require\(['\"]([^'\"]+)['\"]\)"
    ],
    "TypeScript": [
        r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
        r"require\(['\"]([^'\"]+)['\"]\)"
    ],
    "C++": [
        r"#include\s+<([^>]+)>",
        r"#include\s+\"([^\"]+)\""
    ],
    "C": [
        r"#include\s+<([^>]+)>",
        r"#include\s+\"([^\"]+)\""
    ],
    "Java": [
        r"import\s+([\w.]+);"
    ],
    "Go": [
        r"import\s+\"([^\"]+)\""
    ],
    "Rust": [
        r"use\s+([\w:]+)"
    ]
}

# Framework/Library mapping
FRAMEWORK_MAP = {
    "YOLOv8": {
        "languages": ["Python"],
        "patterns": ["ultralytics", "yolo", "YOLO"]
    },
    "OpenCV": {
        "languages": ["Python", "C++", "Java"],
        "patterns": ["cv2", "opencv"]
    },
    "PX4": {
        "languages": ["Python", "C++"],
        "patterns": ["px4", "mavsdk", "MAVSDK", "mavlink", "MAVLink"]
    },
    "React": {
        "languages": ["JavaScript", "TypeScript"],
        "patterns": ["react", "react-dom", "next", "@react"]
    },
    "Vue": {
        "languages": ["JavaScript", "TypeScript"],
        "patterns": ["vue", "@vue"]
    },
    "Angular": {
        "languages": ["TypeScript"],
        "patterns": ["@angular"]
    },
    "FastAPI": {
        "languages": ["Python"],
        "patterns": ["fastapi"]
    },
    "Flask": {
        "languages": ["Python"],
        "patterns": ["flask"]
    },
    "Django": {
        "languages": ["Python"],
        "patterns": ["django"]
    },
    "TensorFlow": {
        "languages": ["Python"],
        "patterns": ["tensorflow", "tf"]
    },
    "PyTorch": {
        "languages": ["Python"],
        "patterns": ["torch", "pytorch"]
    },
    "Pandas": {
        "languages": ["Python"],
        "patterns": ["pandas"]
    },
    "NumPy": {
        "languages": ["Python"],
        "patterns": ["numpy", "np"]
    },
    "ROS": {
        "languages": ["Python", "C++"],
        "patterns": ["rospy", "roscpp", "ros"]
    },
    "Gazebo": {
        "languages": ["Python", "C++"],
        "patterns": ["gazebo"]
    },
    "Tailwind CSS": {
        "languages": ["JavaScript", "TypeScript", "HTML", "CSS"],
        "patterns": ["tailwindcss", "@tailwindcss", "tailwind"]
    },
    "Docker": {
        "languages": ["Python", "JavaScript", "TypeScript", "Dockerfile", "YAML"],
        "patterns": ["docker", "docker-compose"]
    },
    "MongoDB": {
        "languages": ["Python", "JavaScript", "TypeScript"],
        "patterns": ["pymongo", "mongodb", "mongoose", "motor"]
    },
    "Redis": {
        "languages": ["Python", "JavaScript", "TypeScript", "Go"],
        "patterns": ["redis", "aioredis", "ioredis"]
    },
    "PostgreSQL": {
        "languages": ["Python", "JavaScript", "TypeScript", "SQL"],
        "patterns": ["psycopg2", "psycopg", "asyncpg", "pg", "pg-promise"]
    },
    "MySQL": {
        "languages": ["Python", "JavaScript", "TypeScript", "SQL"],
        "patterns": ["mysqlclient", "pymysql", "mysql2", "mysql"]
    },
    "Express.js": {
        "languages": ["JavaScript", "TypeScript"],
        "patterns": ["express"]
    },
    "Next.js": {
        "languages": ["JavaScript", "TypeScript"],
        "patterns": ["next"]
    },
    "Node.js": {
        "languages": ["JavaScript", "TypeScript"],
        "patterns": ["node"]
    }
}


class FrameworkDetector:
    """Detects frameworks and libraries from code imports"""
    
    def __init__(self):
        self.language_map = EXTENSION_TO_LANGUAGE
        self.import_patterns = IMPORT_PATTERNS
        self.framework_map = FRAMEWORK_MAP
    
    def infer_language(self, filename: str) -> Optional[str]:
        """Infer language from file extension"""
        ext = os.path.splitext(filename)[1].lower()
        return self.language_map.get(ext)
    
    def scan_file_for_imports(self, file_content: str, language: str) -> Set[str]:
        """
        Scan first 20 lines for imports.
        
        Args:
            file_content: File content as string
            language: Programming language
        
        Returns:
            Set of import names found
        """
        imports_found = set()
        
        # Get patterns for this language
        patterns = self.import_patterns.get(language, [])
        if not patterns:
            return imports_found
        
        # Scan only first 20 lines (fast & accurate)
        lines = file_content.splitlines()[:20]
        
        for pattern in patterns:
            for line in lines:
                match = re.search(pattern, line)
                if match:
                    # Extract the import name and normalize
                    import_name = match.group(1).lower().strip()
                    imports_found.add(import_name)
        
        return imports_found
    
    
    def detect_frameworks(self, imports: Set[str], language: str) -> List[Dict]:
        """
        Match imports to known frameworks with confidence scoring.
        
        Args:
            imports: Set of import names from code
            language: Programming language
        
        Returns:
            List of detected frameworks with confidence levels
        """
        detections = []
        
        # Load skill ontology
        ontology_path = KNOWLEDGE_DIR / "skill_ontology.json"
        with open(ontology_path, 'r') as f:
            skill_ontology = json.load(f)
        
        for fw_name, fw_config in self.framework_map.items():
            # Skip if no ontology entry
            if fw_name not in skill_ontology:
                continue
            
            ontology = skill_ontology[fw_name]
            
            # Check if language matches native language
            is_native = language in ontology.get("native_languages", [])
            
            # Check verification methods (native implementation)
            if is_native and "verification_methods" in ontology:
                verification_patterns = ontology["verification_methods"].get(language, [])
                for pattern in verification_patterns:
                    # Extract just the import name from patterns like "import cv2" → "cv2"
                    pattern_parts = pattern.lower().split()
                    # Get the last part (the actual module name)
                    pattern_name = pattern_parts[-1] if pattern_parts else pattern.lower()
                    
                    for imp in imports:
                        if pattern_name in imp:
                            detections.append({
                                "skill": fw_name,
                                "confidence": "high",
                                "confidence_score": ontology.get("confidence_weight", 1.0),
                                "evidence_type": "implementation",
                                "reason": f"Native {language} implementation detected"
                            })
                            break
                    else:
                        continue
                    break
            
            # Check interface patterns (using, not implementing)
            if "interface_patterns" in ontology:
                interface_patterns = ontology["interface_patterns"].get(language, [])
                for pattern in interface_patterns:
                    pattern_lower = pattern.lower()
                    for imp in imports:
                        if pattern_lower in imp:
                            detections.append({
                                "skill": fw_name,
                                "confidence": "low",
                                "confidence_score": 0.3,
                                "evidence_type": "interface_only",
                                "reason": f"Interface/client usage in {language}, not native implementation"
                            })
                            break
                    else:
                        continue
                    break
        
        return detections

    
    def scan_dependencies(self, dependency_file: str, language: str) -> List[str]:
        """
        Scan dependency files (requirements.txt, package.json, etc.)
        
        Args:
            dependency_file: Dependency file content
            language: Programming language
        
        Returns:
            List of detected frameworks
        """
        frameworks = []
        
        if language == "Python":
            # Parse requirements.txt / pyproject.toml
            for line in dependency_file.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract package name (before ==, >=, etc.)
                    pkg = re.split(r'[=<>!]', line)[0].strip().lower()
                    
                    # Check against framework patterns
                    for fw_name, fw_config in self.framework_map.items():
                        if "Python" not in fw_config["languages"]:
                            continue
                        for pattern in fw_config["patterns"]:
                            if pattern.lower() in pkg:
                                frameworks.append(fw_name)
                                break
        
        elif language in ["JavaScript", "TypeScript"]:
            # Parse package.json
            try:
                import json
                data = json.loads(dependency_file)
                deps = data.get("dependencies", {})
                deps.update(data.get("devDependencies", {}))
                
                for dep_name in deps.keys():
                    dep_lower = dep_name.lower()
                    
                    # Check against framework patterns
                    for fw_name, fw_config in self.framework_map.items():
                        if language not in fw_config["languages"]:
                            continue
                        for pattern in fw_config["patterns"]:
                            if pattern.lower() in dep_lower:
                                frameworks.append(fw_name)
                                break
            except:
                pass
        
        return frameworks
