# neural_motion_core.py
from typing import Dict, List, Any, Optional, Callable

# --- Action Plan Constants ---
ACTION_HOLD_POSITION: str = "Maintain current state and observe"
ACTION_INITIATE_COMMUNICATION: str = "Initiate communication protocol"
ACTION_ADJUST_PARAMETERS: str = "Adjust internal system parameters for optimization"
ACTION_NEUTRALIZE_TARGET: str = "Target and neutralize identified entity"
ACTION_APPROACH_TARGET: str = "Navigate towards designated target or area"
ACTION_PASSIVE_OBSERVATION: str = "Engage passive observation and data gathering mode"
ACTION_VERIFY_INFORMATION: str = "Cross-reference and verify incoming information"

# --- Motor Profile Constants ---
MOTOR_PROFILE_NONE: str = "none" # No specific motor action required
MOTOR_PROFILE_SPEECH: str = "speech_synthesis_articulation"
MOTOR_PROFILE_DIGITAL: str = "digital_command_execution"
MOTOR_PROFILE_PHYSICAL_MANIPULATION: str = "physical_manipulation_actuators"
MOTOR_PROFILE_LOCOMOTION: str = "locomotion_system_engagement"
MOTOR_PROFILE_SENSORIAL_ADJUSTMENT: str = "sensorial_array_adjustment"

# --- Keyword Constants for Matching ---
# Hypothesis Keywords
KW_HYP_COMMUNICATE: str = "communicate"
KW_HYP_OPTIMIZE: str = "optimize"
KW_HYP_DESTROY: str = "destroy"
KW_HYP_DISABLE: str = "disable"
KW_HYP_APPROACH: str = "approach"
KW_HYP_OBSERVE: str = "observe"
KW_HYP_VERIFY: str = "verify"

# Goal Type Keywords
KW_GOAL_ESTABLISH_CONTACT: str = "establish connection" # Example for goal_type
KW_GOAL_ENHANCE: str = "enhance process" # Example for goal_type

# --- Action Rule Definition Structure ---
# Each rule is a dictionary defining conditions and the resulting action.
# 'condition_check': A function (lambda) that takes (hypothesis_lower, goal_type_lower) and returns bool.
# 'action_plan': The string constant for the action plan.
# 'motor_profile': The string constant for the motor profile.
# 'execution_ready_check': A function (lambda) that takes (context_flags) and returns bool.

ACTION_RULES: List[Dict[str, Any]] = [
    {
        "condition_check": lambda hyp_l, gt_l: KW_HYP_COMMUNICATE in hyp_l or KW_GOAL_ESTABLISH_CONTACT in gt_l,
        "action_plan": ACTION_INITIATE_COMMUNICATION,
        "motor_profile": MOTOR_PROFILE_SPEECH,
        "execution_ready_check": lambda ctx: ctx.get("communication_channel_available", True), # Example: check if comms channel is up
    },
    {
        "condition_check": lambda hyp_l, gt_l: KW_HYP_OPTIMIZE in hyp_l or KW_GOAL_ENHANCE in gt_l,
        "action_plan": ACTION_ADJUST_PARAMETERS,
        "motor_profile": MOTOR_PROFILE_DIGITAL,
        "execution_ready_check": lambda ctx: ctx.get("system_stable_for_adjustment", True), # Example check
    },
    {
        "condition_check": lambda hyp_l, gt_l: KW_HYP_DESTROY in hyp_l or KW_HYP_DISABLE in hyp_l,
        "action_plan": ACTION_NEUTRALIZE_TARGET,
        "motor_profile": MOTOR_PROFILE_PHYSICAL_MANIPULATION, # Or could be digital for cyber targets
        "execution_ready_check": lambda ctx: ctx.get("threat_confirmed", False) and ctx.get("authorization_received", False), # Stricter check
    },
    {
        "condition_check": lambda hyp_l, gt_l: KW_HYP_APPROACH in hyp_l,
        "action_plan": ACTION_APPROACH_TARGET,
        "motor_profile": MOTOR_PROFILE_LOCOMOTION,
        "execution_ready_check": lambda ctx: ctx.get("path_clear", True), # Example: navigation path is clear
    },
    {
        "condition_check": lambda hyp_l, gt_l: KW_HYP_OBSERVE in hyp_l,
        "action_plan": ACTION_PASSIVE_OBSERVATION,
        "motor_profile": MOTOR_PROFILE_SENSORIAL_ADJUSTMENT,
        "execution_ready_check": lambda ctx: True, # Observation is generally always ready
    },
     {
        "condition_check": lambda hyp_l, gt_l: KW_HYP_VERIFY in hyp_l,
        "action_plan": ACTION_VERIFY_INFORMATION,
        "motor_profile": MOTOR_PROFILE_DIGITAL, # Assuming verification is a digital/computational task
        "execution_ready_check": lambda ctx: ctx.get("data_sources_available", True),
    },
]


def plan_action(
    hypothesis: str,
    goal: Dict[str, Any],
    context_flags: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Plans a basic action strategy based on the current hypothesis, goal, and context.

    Args:
        hypothesis (str): The hypothesis string, analyzed for keywords.
        goal (Dict[str, Any]): The goal dictionary. Expected to have "goal_type" (str, optional).
        context_flags (Optional[Dict[str, Any]]): Contextual flags relevant to action execution.
            Examples: "threat_confirmed" (bool), "authorization_received" (bool).

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "action_plan" (str): The determined action plan.
            - "motor_profile" (str): The necessary motor profile for the action.
            - "execution_ready" (bool): Whether the action is deemed ready for execution based on context.
            - "reasoning_log" (List[str]): Log of how the decision was made (optional).
    """
    if context_flags is None:
        context_flags = {}

    processed_hypothesis: str = hypothesis.lower()
    goal_type_str: str = goal.get("goal_type", "").lower()

    action_to_take: str = ACTION_HOLD_POSITION # Default action
    motor_profile_to_use: str = MOTOR_PROFILE_NONE # Default motor profile
    is_execution_ready: bool = True # Default to true, specific rules can override
    
    # Iterate through rules to find a matching action
    for rule in ACTION_RULES:
        if rule["condition_check"](processed_hypothesis, goal_type_str):
            action_to_take = rule["action_plan"]
            motor_profile_to_use = rule["motor_profile"]
            is_execution_ready = rule["execution_ready_check"](context_flags)
            break  # First matching rule determines the action

    return {
        "action_plan": action_to_take,
        "motor_profile": motor_profile_to_use,
        "execution_ready": is_execution_ready,
    }