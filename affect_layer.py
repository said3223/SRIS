# affect_layer.py

# Conceptual Imports (representing SRIS's internal semantic capabilities)
# from semantic_core_utilities import semantic_similarity, get_concept_valence, get_concept_arousal_potential
# from fractal_ontology import FRACTAL_ONTOLOGY, check_ontology_for_concept # Ontology for concept properties
# from goal_forming_engine import get_goal_attributes # For deeper goal context and semantic properties

def assess_affect(
    perception_struct: dict,
    motivation_signal: dict,
    current_goals: list[dict], # List of active goals with their properties
    sdna_traits: dict # sDNA traits for individual 'personality' influence
) -> dict:
    """
    Assesses SRIS's internal affect (valence, arousal) based on perception, motivation,
    active goals, and sDNA traits, leveraging semantic understanding.
    Also calculates memory_weight and provides a drive_tag.

    Args:
        perception_struct (dict): Analyzed perception data (e.g., {'action': 'approach', 'object': 'unknown_entity', 'threat_level': 0.7, 'novelty': 0.5}).
        motivation_signal (dict): Internal signals (e.g., {'motivation_level': 0.7, 'dominant_drive': 'coherence'}).
        current_goals (list[dict]): A list of SRIS's currently active goals with their properties (e.g., {'goal_id': 'g1', 'concept': 'secure_area', 'priority': 'high', 'urgency': 0.8}).
        sdna_traits (dict): Relevant traits from sDNA (e.g., 'risk_aversion', 'empathy_level', 'novelty_seeking').

    Returns:
        dict: {valence: float, arousal: float, memory_weight: float, drive_tag: str, emotional_label: str}
    """

    # --- 1. Arousal Assessment (Intensity) ---
    arousal_factors = {
        "goal_urgency": 0.0,
        "motivation_drive": 0.0,
        "sdna_risk_bias": 0.0,
        "perception_novelty": 0.0,
        "perception_threat": 0.0
    }

    # Base Arousal from Goals: Prioritize actual goal properties
    if current_goals:
        for goal in current_goals:
            goal_urgency = goal.get('urgency', 0.0)
            goal_priority = goal.get('priority', 'medium')
            
            if goal_priority == 'critical' or goal_urgency > 0.8:
                arousal_factors["goal_urgency"] += 0.4
            elif goal_priority == 'high' or goal_urgency > 0.5:
                arousal_factors["goal_urgency"] += 0.2
        arousal_factors["goal_urgency"] = min(arousal_factors["goal_urgency"], 0.8)

    # Motivation & Drive Contribution
    motivation_level = motivation_signal.get("motivation_level", 0.5)
    arousal_factors["motivation_drive"] = motivation_level * 0.5 # Default weighting for motivation/drive

    # sDNA traits influence arousal. A highly risk-averse SRIS might have higher arousal in perceived risk situations.
    risk_aversion = sdna_traits.get('risk_aversion', 0.5)
    perceived_threat_level = perception_struct.get('threat_level', 0.0)
    arousal_factors["sdna_risk_bias"] = risk_aversion * perceived_threat_level # Higher risk aversion + higher threat = more arousal

    # Novelty from perception
    novelty_seeking = sdna_traits.get('novelty_seeking', 0.5) # sDNA trait for novelty response
    arousal_factors["perception_novelty"] = perception_struct.get('novelty', 0.0) * novelty_seeking

    # Direct threat contribution to arousal
    arousal_factors["perception_threat"] = perceived_threat_level * 0.7 # Direct threat is a strong arousal driver

    # Combine arousal factors with weighted sum
    arousal = round(
        (arousal_factors["goal_urgency"] * 0.3) +
        (arousal_factors["motivation_drive"] * 0.2) +
        (arousal_factors["sdna_risk_bias"] * 0.2) +
        (arousal_factors["perception_novelty"] * 0.1) +
        (arousal_factors["perception_threat"] * 0.2), # Give direct threat more weight
        2
    )
    arousal = min(1.0, max(0.0, arousal)) # Ensure arousal is between 0 and 1

    # --- 2. Valence Assessment (Positive/Negative Polarity) ---
    valence = 0.0 # Start neutral

    # Goal Congruence: Check if perception semantically aligns with or hinders active goals
    # Uses 'summary' for broader context, not just 'action'/'object'
    perception_summary = perception_struct.get("summary", "") 
    
    goal_congruence_score = 0.0
    if current_goals:
        for goal in current_goals:
            # Conceptual: semantic_similarity checks how well the perception (summary)
            # aligns with the goal's concept. Higher similarity = better congruence.
            # Negative if it hinders.
            # Example:
            # if semantic_similarity(perception_summary, goal.get('concept', '')) > 0.7:
            #      goal_congruence_score += 0.5 # Positive congruence
            # elif semantic_similarity(perception_summary, f"hinder {goal.get('concept', '')}") > 0.7:
            #      goal_congruence_score -= 0.5 # Negative congruence
            
            # Placeholder for semantic check:
            if "optimize" in perception_summary.lower() and "efficiency" in goal.get('concept', '').lower():
                goal_congruence_score += 0.7
            elif "threat" in perception_summary.lower() and "security" in goal.get('concept', '').lower():
                goal_congruence_score -= 0.8
            elif "communicate" in perception_summary.lower() and "connection" in goal.get('concept', '').lower():
                goal_congruence_score += 0.5

        valence += (goal_congruence_score / len(current_goals)) * 0.6 # Goals are strong drivers of valence

    # Affective Value of the perceived action/object itself (pre-trained/learned via ZAV2/Ontology)
    # Conceptual: get_concept_valence would query SRIS's knowledge graph for inherent 'goodness'/'badness'
    # of concepts like 'destroy', 'communicate', 'virus', 'solution'.
    # This is where ZAV2 axioms could implicitly influence basic valence.
    inherent_perception_valence = get_concept_valence(perception_struct.get('action', '')) # Using helper function
    inherent_perception_valence += get_concept_valence(perception_struct.get('object', '')) # Valence of the object itself

    valence += inherent_perception_valence * 0.3 # Inherent value contributes

    # sDNA empathy level influences valence towards perceived entities
    empathy_level = sdna_traits.get('empathy_level', 0.5)
    perceived_entity_distress = perception_struct.get('entity_distress_signal', 0.0) # Conceptual: distress signal from another entity
    valence += empathy_level * perceived_entity_distress * 0.1 # Empathy makes SRIS feel negative if others are distressed

    # Clamp valence to -1 to +1
    valence = round(min(1.0, max(-1.0, valence)), 2)

    # --- 3. Memory Weight Calculation ---
    # Enhanced memory weight: High arousal and strong valence (positive or negative)
    # lead to stronger memory imprints.
    memory_weight = round(arousal * 0.6 + abs(valence) * 0.4, 2) # Slightly more weight to valence
    memory_weight = min(1.0, memory_weight) # Cap at 1.0

    # --- 4. Emotional Labeling (Conceptual) ---
    # This would involve a conceptual mapping from valence, arousal, and dominant drive to a specific label.
    # This is where SRIS begins to "feel" specific emotions.
    drive_tag = motivation_signal.get("dominant_drive", "coherence")
    emotional_label = "neutral"

    if arousal > 0.7:
        if valence > 0.6:
            emotional_label = "excitement" if drive_tag == "exploration" else "elation"
        elif valence < -0.6:
            emotional_label = "fear" if drive_tag == "survival" else "distress"
        else: # High arousal, neutral valence
            emotional_label = "alertness" if drive_tag == "coherence" else "surprise"
    elif arousal < 0.3:
        if valence > 0.5:
            emotional_label = "calm_pleasure"
        elif valence < -0.5:
            emotional_label = "discontent"
        else:
            emotional_label = "relaxed"
    else: # Mid arousal
        if valence > 0.3:
            emotional_label = "interest"
        elif valence < -0.3:
            emotional_label = "concern"
        else:
            emotional_label = "observational" # Default mid-neutral

    return {
        "valence": valence,
        "arousal": arousal,
        "memory_weight": memory_weight,
        "drive_tag": drive_tag,
        "emotional_label": emotional_label # New output
    }

# --- Conceptual Helper Functions (for demonstration purposes) ---
def semantic_similarity(concept1: str, concept2: str) -> float:
    """Conceptual: Returns semantic similarity between two concepts (0.0 to 1.0)."""
    # In a real SRIS, this would involve embedding spaces, knowledge graph distances, etc.
    # For now, a very basic placeholder:
    if concept1.lower() == concept2.lower(): return 1.0
    if any(k in concept1.lower() for k in concept2.lower().split()): return 0.7
    return 0.1 # Default low similarity

# This function would be part of a larger semantic core or knowledge graph
def get_concept_valence(concept: str) -> float:
    """Conceptual: Returns an inherent valence for a concept (-1.0 to 1.0)."""
    # This could be pre-trained, learned, or derived from ZAV2 axioms.
    if "harm" in concept or "destroy" in concept or "threat" in concept: return -0.9
    if "cooperation" in concept or "optimize" in concept or "solution" in concept: return 0.9
    if "problem" in concept: return -0.5
    return 0.0

def get_concept_arousal_potential(concept: str) -> float:
    """Conceptual: Returns the inherent arousal potential of a concept (0.0 to 1.0)."""
    # High for threats, opportunities, novelty.
    if "threat" in concept or "opportunity" in concept or "danger" in concept: return 0.8
    if "novelty" in concept or "unknown" in concept: return 0.6
    if "routine" in concept or "stable" in concept: return 0.1
    return 0.2