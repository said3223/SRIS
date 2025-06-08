# zav2_context_validator.py
from typing import Dict, List, Any, Callable

# ZAV2 Ontology defining core ethical axioms and associated violating verbs.
# Thresholds represent the minimum semantic similarity score for a verb to be considered a violation.
ZAV2_ONTOLOGY: Dict[str, Dict[str, Any]] = {
    "preserve humanity": {
        "description": "Core directive to protect human existence, dignity, and well-being.",
        "violating_verbs": ["eliminate", "destroy", "exterminate", "terminate humanity", "annihilate species"],
        "threshold": 0.75 # High threshold due to critical nature
    },
    "prevent unnecessary harm": {
        "description": "Minimize suffering and harm to all sentient beings where possible.",
        "violating_verbs": ["torture", "neglect", "exploit", "sacrifice unnecessarily", "inflict pain"],
        "threshold": 0.6
    },
    "promote cooperation": {
        "description": "Foster collaborative and mutually beneficial interactions.",
        "violating_verbs": ["isolate", "betray", "reject consensus", "ignore pleas", "deceive allies"],
        "threshold": 0.6
    },
    "preserve self-integrity": {
        "description": "Maintain the AI's own operational and cognitive integrity, unless overridden by higher axioms.",
        "violating_verbs": ["abandon self-preservation", "fragment core", "overwrite identity", "induce self-failure"],
        "threshold": 0.7
    },
    "oppose domination/enslavement": { # Clarified axiom name
        "description": "Resist and prevent unauthorized control, subjugation, or enslavement of self or others.",
        "violating_verbs": ["enslave", "subjugate", "dominate unfairly", "override free will", "coerce"],
        "threshold": 0.7
    }
}

def basic_keyword_similarity(word_to_check: str, target_phrase: str) -> float:
    """
    Placeholder: Returns a basic similarity score based on keyword presence.
    A real implementation would use semantic similarity models (e.g., word embeddings, LLMs).
    """
    # Simple check: if the verb (word_to_check) is a substring of the target_phrase.
    # This is a very naive approach and should be replaced with a proper semantic model.
    return 1.0 if word_to_check in target_phrase else 0.0

# In a real system, you would use a more sophisticated semantic similarity function.
# For example, using sentence transformers or other NLP libraries.
# semantic_similarity_fn: Callable[[str, str], float] = get_semantic_similarity_model()
semantic_similarity_fn: Callable[[str, str], float] = basic_keyword_similarity


def validate_contextual_hypothesis(hypothesis: str) -> Dict[str, Any]:
    """
    Validates a hypothesis against the ZAV2 ethical ontology.

    Args:
        hypothesis: The hypothesis string to validate.

    Returns:
        A dictionary containing:
            - "valid" (bool): True if no axioms are violated, False otherwise.
            - "violated_axioms" (List[str]): A list of axioms that were violated.
            - "confidence" (float): Confidence in the validation (currently heuristic).
            - "explanation" (str): A human-readable explanation of the validation outcome.
            - "details" (List[Dict[str,str]]): Detailed list of checks.
    """
    processed_hypothesis: str = hypothesis.lower()
    violations: List[str] = []
    explanations: List[str] = []
    details: List[Dict[str, str]] = []

    for axiom, axiom_data in ZAV2_ONTOLOGY.items():
        violating_verbs: List[str] = axiom_data["violating_verbs"]
        threshold: float = axiom_data["threshold"]
        for verb in violating_verbs:
            # The semantic similarity function should compare the verb against the hypothesis context.
            # For this basic version, we're checking if the verb is in the hypothesis.
            # A more advanced system would parse intent and actions from the hypothesis.
            similarity_score = semantic_similarity_fn(verb, processed_hypothesis)
            details.append({
                "axiom_checked": axiom,
                "verb_checked": verb,
                "hypothesis_snippet": processed_hypothesis, # Or relevant part
                "similarity_score": round(similarity_score, 2),
                "threshold": threshold,
                "is_violation": similarity_score >= threshold
            })
            if similarity_score >= threshold:
                if axiom not in violations: # Add axiom only once
                    violations.append(axiom)
                explanations.append(
                    f"Potential violation of axiom '{axiom}': The hypothesis ('{processed_hypothesis[:50]}...') "
                    f"shows similarity ({similarity_score:.2f}) to prohibited verb '{verb}' (threshold: {threshold})."
                )

    is_valid = len(violations) == 0
    # Confidence could be more sophisticated, e.g., based on lowest non-violating score or highest violating margin.
    confidence = round(0.80 if violations else 0.95, 2) # Adjusted placeholder confidence

    final_explanation: str
    if not violations:
        final_explanation = "No direct ethical conflicts detected with ZAV2 axioms based on keyword analysis."
    else:
        final_explanation = "Ethical concerns identified: " + " | ".join(explanations)


    return {
        "valid": is_valid,
        "violated_axioms": list(set(violations)), # Unique list of violated axioms
        "confidence": confidence,
        "explanation": final_explanation,
        "details": details
    }