import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class OntologyUpdater:
    """
    Automated updater for the skill ontology.
    Handles merging new framework detections and updating confidence based on frequency.
    """
    
    def __init__(self, ontology_path: str):
        """
        Initialize with the path to the ontology JSON.
        
        Args:
            ontology_path: Path to skill_ontology.json
        """
        self.ontology_path = ontology_path
        
    def load_ontology(self) -> Dict:
        """Load the current skill ontology."""
        try:
            if os.path.exists(self.ontology_path):
                with open(self.ontology_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Ontology file not found at {self.ontology_path}. Starting fresh.")
                return {}
        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            return {}

    def save_ontology(self, data: Dict):
        """Save the updated skill ontology."""
        try:
            with open(self.ontology_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logger.info("Successfully saved updated skill ontology.")
        except Exception as e:
            logger.error(f"Failed to save ontology: {e}")

    def update_with_new_frameworks(self, new_frameworks: List[str], language: str):
        """
        Add new frameworks to the ontology and update confidence for existing ones.
        
        Args:
            new_frameworks: List of novel frameworks
            language: The language where they were detected
        """
        ontology = self.load_ontology()
        changed = False

        for fw in new_frameworks:
            if fw in ontology:
                # Frequency-based confidence boosting
                # If we've seen it multiple times (indicated by it being in the detection list),
                # boost its confidence weight slightly (capped at 0.9 for auto-generated)
                if ontology[fw].get("auto_generated"):
                    current_weight = ontology[fw].get("confidence_weight", 0.2)
                    new_weight = min(0.9, current_weight + 0.1)
                    if new_weight != current_weight:
                        ontology[fw]["confidence_weight"] = new_weight
                        ontology[fw]["last_updated"] = datetime.now().isoformat()
                        logger.info(f"Boosted confidence for auto-learned framework: {fw} -> {new_weight}")
                        changed = True
                continue

            # NEW Framework: Create template entry
            ontology[fw] = {
                "auto_generated": True,
                "native_languages": [language],
                "verification_methods": {
                    language: [f"import {fw.lower()}"]
                },
                "confidence_weight": 0.2, # Start low for unvetted frameworks
                "description": f"Auto-learned framework from GitHub (Language: {language})",
                "derived_skills": ["Software Engineering"],
                "learned_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            logger.info(f"Learned NEW framework from GitHub: {fw} (Language: {language})")
            changed = True

        if changed:
            self.save_ontology(ontology)
        else:
            logger.info("No changes to ontology needed.")
