try:
    from .utils.ontology_loader import SKILL_DB
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from utils.ontology_loader import SKILL_DB

def classify_skill(skill):
    """
    Classify a skill into categories based on the ontology.
    
    Returns:
        "framework" if the skill exists in the ontology DB.
        "language" if it's a known programming language.
        "other" otherwise.
    """
    # Exact match in ontology means it's a framework or system we track
    if skill in SKILL_DB:
        return "framework"

    # Common languages fallback
    languages = [
        "python", "javascript", "typescript", "c++", "cpp", "c#", "java", 
        "go", "rust", "ruby", "php", "swift", "kotlin", "sql", "html", "css"
    ]
    if skill.lower() in languages:
        return "language"

    return "other"
