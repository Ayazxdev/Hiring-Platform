import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_ontology():
    """Load the skill ontology from JSON file."""
    # Try different paths to find the ontology
    possible_paths = [
        Path(__file__).parent.parent / "knowledge" / "skill_ontology.json",
        Path("skill_verification_agent/knowledge/skill_ontology.json"),
        Path("knowledge/skill_ontology.json"),
        Path(__file__).parent / "skill_ontology.json"
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    logger.info(f"Loaded skill ontology from {path}")
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read ontology from {path}: {e}")
                
    logger.warning("Skill ontology not found. Using empty database.")
    return {}

SKILL_DB = load_ontology()
