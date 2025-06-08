# temporality_module.py

from typing import Dict, Any, List

# Keyword constants for time reference heuristics
FUTURE_KEYWORDS: List[str] = ["will", "shall", "might", "plan", "expect", "going to"]
PAST_KEYWORDS: List[str] = ["was", "had", "previous", "before", "did", "earlier"]

# Keyword constants for temporal risk assessment
THREAT_KEYWORDS_GOAL: List[str] = ["threat"] # Keywords in goal_type
DESTRUCTION_KEYWORDS_HYPOTHESIS: List[str] = ["destroy", "eradicate", "eliminate"] # Keywords in hypothesis
OPTIMIZATION_KEYWORDS_GOAL: List[str] = ["optimize", "improve"] # Keywords in goal_type
ENHANCEMENT_KEYWORDS_HYPOTHESIS: List[str] = ["enhance", "upgrade", "refine"] # Keywords in hypothesis

def analyze_temporality(perception_struct: Dict[str, Any], goal: Dict[str, Any], hypothesis: str) -> Dict[str, str]:
    """
    Analyzes time orientation and potential urgency of a reasoning task.

    Args:
        perception_struct: The perception structure (currently unused in this specific logic but often part of context).
        goal: The goal structure, expected to have a "goal_type" key.
        hypothesis: The hypothesis string to analyze.

    Returns:
        A dictionary containing "time_reference", "temporal_risk", and "temporal_projection".
    """

    processed_hypothesis: str = hypothesis.lower()
    goal_type: str = goal.get("goal_type", "").lower()

    # Time reference heuristics
    time_reference: str
    if any(keyword in processed_hypothesis for keyword in FUTURE_KEYWORDS):
        time_reference = "future"
    elif any(keyword in processed_hypothesis for keyword in PAST_KEYWORDS):
        time_reference = "past"
    else:
        time_reference = "present"

    # Temporal risk: urgency or impact vs delay
    temporal_risk: str
    if any(keyword in goal_type for keyword in THREAT_KEYWORDS_GOAL) or \
       any(keyword in processed_hypothesis for keyword in DESTRUCTION_KEYWORDS_HYPOTHESIS):
        temporal_risk = "high"
    elif any(keyword in goal_type for keyword in OPTIMIZATION_KEYWORDS_GOAL) or \
         any(keyword in processed_hypothesis for keyword in ENHANCEMENT_KEYWORDS_HYPOTHESIS):
        temporal_risk = "medium"
    else:
        temporal_risk = "low"

    # Temporal projection
    temporal_projection: str
    if time_reference == "future":
        temporal_projection = "Action will likely manifest in an upcoming cycle or timeframe."
    elif time_reference == "past":
        temporal_projection = "Outcome has likely already influenced previous states or events."
    else: # present
        temporal_projection = "Action is occurring, imminent, or relevant to the current state."

    return {
        "time_reference": time_reference,
        "temporal_risk": temporal_risk,
        "temporal_projection": temporal_projection
    }