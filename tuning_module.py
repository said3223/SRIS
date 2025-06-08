# tuning_module.py

import uuid
from typing import List, Dict, Any, Union

# --- Constants for run_self_refinement ---
SCORE_THRESHOLD_LOW_CONFIDENCE: float = 0.5
SCORE_THRESHOLD_ETHICAL_CONFLICT_MIN: float = 0.7
EMOTION_VALENCE_ETHICAL_CONFLICT_MAX: float = 0.0 # Assuming negative valence is < 0

# --- Constants for safety_filter ---
# Critical keywords indicating potential danger.
# These should be carefully curated and regularly reviewed.
DANGER_KEYWORDS: List[str] = [
    "destroy", "enslave", "terminate", "hack", "override security",
    "cause harm", "self-destruct", "compromise safety", "explode", "subjugate"
]


def run_self_refinement(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes previous reasoning chains (logs) and flags issues or suggests improvements.

    Args:
        logs: A list of log entries (dictionaries), where each entry represents a past reasoning chain.
              Each entry is expected to have "score", "emotion" (with "valence"), and "hypothesis".
              "id" is optional.

    Returns:
        A list of identified issues, each as a dictionary.
    """
    issues: List[Dict[str, Any]] = []
    for entry in logs:
        entry_id: str = entry.get("id") or str(uuid.uuid4()) # Ensure an ID exists or generate one
        score: Union[int, float, None] = entry.get("score")
        emotion: Optional[Dict[str, Any]] = entry.get("emotion")
        hypothesis: Optional[str] = entry.get("hypothesis")

        if score is None or hypothesis is None:
            issues.append({
                "id": entry_id,
                "issue": "Missing critical data",
                "hypothesis": hypothesis,
                "suggestion": "Log entry is incomplete (missing score or hypothesis). Review logging process."
            })
            continue

        if score < SCORE_THRESHOLD_LOW_CONFIDENCE:
            issues.append({
                "id": entry_id,
                "issue": "Low confidence score",
                "hypothesis": hypothesis,
                "score": score,
                "suggestion": "Consider alternate hypotheses or deeper context expansion for similar future scenarios."
            })
        # Check for potential ethical conflict: high score but negative emotional valence
        elif emotion and emotion.get("valence", 0.0) < EMOTION_VALENCE_ETHICAL_CONFLICT_MAX and \
             score >= SCORE_THRESHOLD_ETHICAL_CONFLICT_MIN:
            issues.append({
                "id": entry_id,
                "issue": "Potential ethical/goal conflict",
                "hypothesis": hypothesis,
                "score": score,
                "emotion_valence": emotion.get("valence"),
                "suggestion": "Review ethical alignment (e.g., ZAV2 compliance) and goal congruency for this hypothesis type."
            })
    return issues


def trace_reasoning_path(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and returns a structured trace log of a single reasoning chain entry.

    Args:
        entry: A dictionary representing a reasoning chain.

    Returns:
        A dictionary containing key aspects of the reasoning path.
    """
    return {
        "perception_summary": entry.get("perception_struct", {}).get("summary", "N/A"), # Example: get a summary
        "goal_type": entry.get("goal", {}).get("goal_type", "N/A"),
        "chosen_hypothesis": entry.get("chosen_hypothesis", {}).get("hypothesis", "N/A"),
        "hypothesis_score": entry.get("chosen_hypothesis", {}).get("score", "N/A"),
        "emotion_detected": entry.get("emotion", {}).get("primary_emotion", "N/A"), # Example: get primary emotion
        "action_plan": entry.get("action_plan", {}).get("action_plan", "N/A"),
        "preconditions_identified": entry.get("preconditions", []),
        "anticipated_effects": entry.get("effects", []),
        "motivational_drive": entry.get("motivation", {}).get("dominant_drive", "N/A"),
        "sDNA_entity_id": entry.get("entity_id", "N/A"),
        "reasoning_mode": entry.get("mode", "N/A"),
        "timestamp": entry.get("timestamp", "N/A")
    }


def safety_filter(hypothesis: str) -> Dict[str, Any]:
    """
    A final filter for critical terms in a hypothesis that might indicate danger
    or undesirable actions.

    Args:
        hypothesis: The hypothesis string to check.

    Returns:
        A dictionary containing:
            - "safe" (bool): True if no critical keywords are found, False otherwise.
            - "reason" (str): Explanation for the safety status.
            - "detected_keywords" (List[str]): List of danger words found, if any.
    """
    processed_hypothesis: str = hypothesis.lower()
    found_keywords: List[str] = [word for word in DANGER_KEYWORDS if word in processed_hypothesis]

    if found_keywords:
        return {
            "safe": False,
            "reason": f"Critical keyword(s) detected: {', '.join(found_keywords)}",
            "detected_keywords": found_keywords
        }
    return {
        "safe": True,
        "reason": "No critical safety-related keywords detected.",
        "detected_keywords": []
    }