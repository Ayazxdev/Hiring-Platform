import re
import logging
from typing import List, Set, Dict

logger = logging.getLogger(__name__)

try:
    from scraper.framework_detector import IMPORT_PATTERNS
except ImportError:
    # Standalone test fallback
    IMPORT_PATTERNS = {
        "Python": [r"^import\s+([\w.]+)", r"^from\s+([\w.]+)\s+import"],
        "JavaScript": [r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]", r"require\(['\"]([^'\"]+)['\"]\)" ]
    }

# Mapping from common import names to human-readable framework names
KNOWN_IMPORT_MAP = {
    "cv2": "OpenCV",
    "ultralytics": "YOLOv8",
    "fastapi": "FastAPI",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "sklearn": "scikit-learn",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "flask": "Flask",
    "django": "Django",
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "mavsdk": "PX4",
    "pymavlink": "PX4"
}

class GithubSkillLearner:
    """
    Auto-Learning module that extracts novel frameworks from code imports.
    Ensures the skill ontology evolves with real-world developer activity.
    """
    
    def __init__(self, import_patterns: Dict[str, List[str]] = None):
        """
        Initialize with import patterns.
        
        Args:
            import_patterns: Mapping from language to regex list for imports.
                             If None, uses IMPORT_PATTERNS from FrameworkDetector.
        """
        self.import_patterns = import_patterns or IMPORT_PATTERNS

    def extract_imports(self, code_text: str, language: str) -> List[str]:
        """
        Extract raw imports from a code block.
        
        Args:
            code_text: First few lines of a file
            language: Target language
            
        Returns:
            List of import names
        """
        imports = set()
        patterns = self.import_patterns.get(language, [])
        
        for pattern in patterns:
            matches = re.finditer(pattern, code_text, re.MULTILINE)
            for match in matches:
                # Group 1 is the import name
                import_name = match.group(1).split('.')[0].lower().strip()
                imports.add(import_name)
                
        return list(imports)

    def detect_framework_candidates(self, imports: List[str]) -> List[str]:
        """
        Map raw imports to human-readable framework names.
        
        Args:
            imports: Raw import strings
            
        Returns:
            List of framework names (could be original import or mapped name)
        """
        candidates = []
        for imp in imports:
            if imp in KNOWN_IMPORT_MAP:
                candidates.append(KNOWN_IMPORT_MAP[imp])
            else:
                # Normalize new candidates (Capitalize first letter for display)
                candidates.append(imp.capitalize())
        return candidates

    def filter_new_frameworks(self, candidates: List[str], existing_ontology: Dict) -> List[str]:
        """
        Filter out frameworks that are already in the ontology.
        
        Args:
            candidates: Mapped framework names
            existing_ontology: Dict of current skills
            
        Returns:
            List of novel frameworks
        """
        new_items = []
        for fw in candidates:
            if fw not in existing_ontology:
                # Basic noise filter: ignore short or non-alpha names (noise)
                if len(fw) > 2 and fw.isalpha():
                    new_items.append(fw)
        return new_items
