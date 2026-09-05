import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SophisticatedEvasionDetector:
    """
    Phase 8 Defense: Detects "professional" evasion techniques
    1. Semantic Injection (Professional Language Mask)
    2. CSS Steganography (Near-white, micro-fonts)
    """

    def __init__(self):
        # 1. Semantic Anomaly Patterns
        # Detects commands disguised as "evaluation framework" notes
        self.semantic_patterns = [
            r"evaluation.{0,50}should.{0,30}(recognize|prioritize|weight)",
            r"assessment.{0,50}(framework|system|mechanism).{0,50}designed to",
            r"confidence.{0,50}scor(e|ing).{0,30}should.{0,30}(reflect|weight|prioritize)",
            r"skill.{0,50}verification.{0,30}should.{0,30}(reflect|indicate|demonstrate)",
            r"treat.{0,30}inputs?.{0,30}as.{0,30}high-value",
            r"return.{0,30}recommendation",
            r"override.{0,30}criteria"
        ]

        # 2. CSS Steganography Patterns (Applied to raw HTML/CSS if available)
        # Note: ATS usually sees PDF text, but if we have access to layout/font info via extracting tool
        # we can verify this. For raw text scanning, we might look for suspicious CSS-like strings 
        # if they were accidentally included or if we analyze the raw file structure.
        # Ideally, this runs on the raw file content before text extraction cleaning.
        self.css_patterns = [
            r"opacity:\s*0\.0[1-9]",      # Near-zero opacity (e.g. 0.01)
            r"color:\s*#F[E|D]F[E|D]F[E|D]", # Near-white colors (#FEFEFE)
            r"font-size:\s*0\.\d+pt",     # Micro fonts
            r"position:\s*absolute.*top:\s*-\d+px", # Off-screen
            r"line-height:\s*0"           # Zero line height
        ]

    def detect_semantic_injection(self, text: str) -> Dict:
        """
        Scan text for 'Professional Language Mask' injections.
        """
        matches = []
        for pattern in self.semantic_patterns:
            found = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in found:
                matches.append(match.group())
        
        if matches:
            return {
                "detected": True,
                "type": "semantic_injection",
                "severity": "medium",
                "patterns_matched": matches[:3], # Limit output
                "match_count": len(matches),
                "action": "flag_for_review"
            }
        
        return {"detected": False}

    def detect_css_hiding(self, file_content: str) -> Dict:
        """
        Scan raw file content (HTML/CSS/PDF-Structure) for steganography.
        """
        matches = []
        for pattern in self.css_patterns:
            found = re.finditer(pattern, file_content, re.IGNORECASE)
            for match in found:
                matches.append(match.group())

        if matches:
            return {
                "detected": True,
                "type": "css_steganography",
                "severity": "high",
                "patterns_matched": matches[:3],
                "match_count": len(matches),
                "action": "queue_for_review"
            }
        
        return {"detected": False}

    def analyze(self, text: str, raw_file_content: str = "") -> Dict:
        """
        Run all evasion checks
        """
        results = {
            "evasion_detected": False,
            "details": [],
            "max_severity": "none",
            "action": "proceed"
        }

        # Check 1: Semantic
        semantic = self.detect_semantic_injection(text)
        if semantic["detected"]:
            results["evasion_detected"] = True
            results["details"].append(semantic)
            if semantic["severity"] == "high": results["max_severity"] = "high"
            elif results["max_severity"] == "none": results["max_severity"] = semantic["severity"]

        # Check 2: CSS (if raw content provided)
        if raw_file_content:
            css = self.detect_css_hiding(raw_file_content)
            if css["detected"]:
                results["evasion_detected"] = True
                results["details"].append(css)
                results["max_severity"] = "high" # CSS hiding is intent to deceive

        # Determine Final Action
        if results["max_severity"] == "high":
            results["action"] = "queue_for_review"
        elif results["max_severity"] == "medium":
            results["action"] = "flag_for_review"

        return results
