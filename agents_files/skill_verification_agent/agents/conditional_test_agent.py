
import json
from typing import Dict, List


TEST_THRESHOLD = 70  # Minimum score to upgrade credential


class ConditionalTestAgent:
    """
    Manages the conditional testing phase (Stage 3.2).
    """

    def analyze_credential(self, credential_path: str) -> Dict:
        """
        Entry point.
        Reads credential and determines whether testing is required.
        """
        with open(credential_path, "r") as f:
            envelope = json.load(f)

        # Unwrap Envelope
        if "output" in envelope:
            credential = envelope["output"]
        else:
            credential = envelope

        if not credential.get("test_required", False):
            return {
                "status": "SKIPPED",
                "reason": "Testing not required",
                "credential": credential
            }

        verified_skills = credential.get("verified_skills", [])
        testable_skills = self.identify_testable_skills(verified_skills)

        return {
            "status": "TEST_REQUIRED",
            "test_plan": {
                "skills_to_test": testable_skills
            },
            "credential": credential
        }

    def identify_testable_skills(self, verified_skills: any) -> List[str]:
        """
        Selects skills that should be tested.
        """
        # Flatten if tiered
        if isinstance(verified_skills, dict):
            flat_skills = []
            for tier in verified_skills.values():
                flat_skills.extend(tier)
        else:
            flat_skills = verified_skills

        language_priority = ["Python", "JavaScript", "TypeScript", "C++"]
        domain_priority = ["Computer Vision", "Machine Learning", "Robotics"]

        selected = []

        # 1️⃣ Primary language
        for lang in language_priority:
            if lang in flat_skills:
                selected.append(lang)
                break
            # Case insensitive check
            for s in flat_skills:
                if s.lower() == lang.lower():
                    selected.append(s)
                    break
            if selected: break

        # 2️⃣ Domain skill
        for domain in domain_priority:
            if domain in flat_skills:
                selected.append(domain)
                break
            for s in flat_skills:
                if s.lower() == domain.lower():
                    selected.append(s)
                    break
            if len(selected) > 1: break

        # 3️⃣ Data Structures (implicit from LeetCode / Codeforces)
        selected.append("Data Structures")

        return selected

    def update_with_results(self, credential_path: str, test_score: int) -> Dict:
        """
        Updates credential after test completion.
        """
        with open(credential_path, "r") as f:
            envelope = json.load(f)

        # Unwrap Envelope
        if "output" in envelope:
            credential = envelope["output"]
        else:
            credential = envelope

        credential["evidence"]["test_score"] = test_score

        if test_score >= TEST_THRESHOLD:
            credential["credential_status"] = "VERIFIED"
            credential["signal_strength"] = "strong"
            credential["test_required"] = False
            credential["next_stage"] = "bias_detection"
        else:
            credential["credential_status"] = "VERIFIED_WITH_FLAGS"
            credential["next_stage"] = "interview"
        
        # If wrapped, update content inside envelope
        if "output" in envelope:
            envelope["output"] = credential
            return envelope
        
        return credential
