# motivation_engine.py
from typing import Dict, List, Any, Optional

# --- Configuration Constants ---
# Base values and factors
BASELINE_MOTIVATION: float = 0.5
SURVIVAL_BOOST: float = 0.3
PRESERVATION_ETHICS_FACTOR: float = 0.2  # Influence of ethics sensitivity on preservation drive
EXPLORATION_ADAPTIVITY_FACTOR: float = 0.2 # Influence of adaptivity on exploration drive
OPTIMIZATION_DEDUCTIVE_BOOST: float = 0.15 # Increased boost for deductive style in optimization
OPTIMIZATION_DEFAULT_BOOST: float = 0.05

# Contextual modifiers
EXTERNAL_ALERT_BOOST: float = 0.2
LOW_SUCCESS_PENALTY: float = -0.15 # Made penalty negative for clarity
INTERNAL_ERROR_PENALTY: float = -0.2 # Example: if system detects internal errors

# Thresholds for recommendations
FOCUS_BOOST_THRESHOLD: float = 0.75 # Adjusted threshold
URGENCY_FLAG_THRESHOLD: float = 0.65 # Adjusted threshold
ETHICAL_CAUTION_SENSITIVITY_THRESHOLD: float = 0.7 # sDNA ethics_sensitivity threshold for caution

# Drive mapping from goal_type to dominant drive
DRIVE_MAP: Dict[str, str] = {
    "analyze proximity": "exploration",
    "evaluate threat": "survival",
    "enhance process": "optimization",
    "establish connection": "cooperation", # Assuming cooperation is a valid drive
    "evaluate ethical risk": "preservation",
    "analyze situation": "coherence",
    "maintain stability": "homeostasis" # Example of another drive
}
DEFAULT_DRIVE: str = "coherence" # Default drive if goal_type is not mapped

# sDNA default values
DEFAULT_ADAPTIVITY: float = 0.5
DEFAULT_ETHICS_SENSITIVITY: float = 0.5
DEFAULT_THINKING_STYLE: str = "deductive"


def evaluate_motivation(
    goal_type: str,
    sdna: Dict[str, Any],
    context_flags: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculates a motivation signal based on the goal type, sDNA profile, and contextual flags.

    Args:
        goal_type (str): The type of goal being pursued (e.g., "evaluate threat").
        sdna (Dict[str, Any]): The agent's semantic DNA profile. Expected keys:
            - "adaptivity" (float, optional): Agent's adaptability level (0.0-1.0).
            - "ethics_sensitivity" (float, optional): Agent's sensitivity to ethical considerations (0.0-1.0).
            - "thinking_style" (str, optional): Agent's cognitive style (e.g., "deductive", "inductive").
        context_flags (Optional[Dict[str, Any]]): Contextual flags affecting motivation. Expected keys:
            - "external_alert" (bool, optional): True if an external alert is active.
            - "low_success_rate" (bool, optional): True if recent task success rate is low.
            - "internal_error_detected" (bool, optional): True if internal system errors are present.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "dominant_drive" (str): The activated dominant motivational drive.
            - "motivation_level" (float): The calculated motivation level (0.0-1.0), rounded.
            - "recommendations" (List[str]): A list of modulation tags (e.g., "focus_boost", "urgency_flag").
    """

    if context_flags is None:
        context_flags = {}

    # Extract sDNA parameters with defaults
    adaptivity: float = sdna.get("adaptivity", DEFAULT_ADAPTIVITY)
    ethics_sensitivity: float = sdna.get("ethics_sensitivity", DEFAULT_ETHICS_SENSITIVITY)
    thinking_style: str = sdna.get("thinking_style", DEFAULT_THINKING_STYLE)

    # Determine base drive
    dominant_drive: str = DRIVE_MAP.get(goal_type.lower(), DEFAULT_DRIVE) # Use .lower() for robustness

    # Initialize motivation
    motivation_score: float = BASELINE_MOTIVATION

    # Apply drive-specific boosts based on sDNA and goal
    if dominant_drive == "survival":
        motivation_score += SURVIVAL_BOOST
    elif dominant_drive == "preservation":
        motivation_score += PRESERVATION_ETHICS_FACTOR * ethics_sensitivity
    elif dominant_drive == "exploration":
        motivation_score += EXPLORATION_ADAPTIVITY_FACTOR * adaptivity
    elif dominant_drive == "optimization":
        if thinking_style == "deductive":
            motivation_score += OPTIMIZATION_DEDUCTIVE_BOOST
        else:
            motivation_score += OPTIMIZATION_DEFAULT_BOOST
    # Add other drive calculations as needed (e.g., cooperation, homeostasis)

    # Apply contextual modifiers
    if context_flags.get("external_alert", False):
        motivation_score += EXTERNAL_ALERT_BOOST
    if context_flags.get("low_success_rate", False):
        motivation_score += LOW_SUCCESS_PENALTY # Note: LOW_SUCCESS_PENALTY is negative
    if context_flags.get("internal_error_detected", False):
        motivation_score += INTERNAL_ERROR_PENALTY # Note: INTERNAL_ERROR_PENALTY is negative

    # Clamp motivation score to the range [0.0, 1.0]
    motivation_score = min(1.0, max(0.0, motivation_score))

    # Generate recommendations based on motivation and drive
    recommendations: List[str] = []
    if motivation_score > FOCUS_BOOST_THRESHOLD:
        recommendations.append("focus_boost")

    if dominant_drive in ["survival", "preservation"] and motivation_score > URGENCY_FLAG_THRESHOLD:
        recommendations.append("urgency_flag")

    # Ethical caution recommendation can be based on the drive and explicit sDNA sensitivity
    if dominant_drive == "preservation" and ethics_sensitivity > ETHICAL_CAUTION_SENSITIVITY_THRESHOLD:
        recommendations.append("ethical_caution")
    elif ethics_sensitivity > 0.85 : # General high ethics sensitivity might also warrant caution
         if "ethical_caution" not in recommendations:
            recommendations.append("general_ethical_vigilance")


    return {
        "dominant_drive": dominant_drive,
        "motivation_level": round(motivation_score, 3), # Increased precision
        "recommendations": recommendations
    }