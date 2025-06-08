# fractal_ontology.py

# Концептуальная Фрактальная Онтология:
# Это не просто список слов, а ссылка на внутренний граф знаний SRIS.
# 'concepts' могут иметь атрибуты, связи с другими понятиями, и правила.
# 'sub_domains' указывают на иерархию и наследование правил.
# 'properties' могут включать "inherent_valence", "arousal_potential", "required_capabilities", etc.
FRACTAL_ONTOLOGY_STRUCTURE = {
    "concept_system": {
        "description": "Any defined system SRIS interacts with.",
        "properties": {"type": "abstract_entity"},
        "sub_concepts": {
            "concept_system_operational": {"keywords": ["system", "process", "network"], "properties": {"status": "active"}},
            "concept_system_maintenance": {"keywords": ["maintenance", "repair", "diagnostic"], "properties": {"function": "support"}},
            "concept_system_self_preservation": {"keywords": ["self-repair", "self-defense"], "properties": {"priority": "critical"}}
        }
    },
    "domain_interaction": {
        "description": "Concepts related to inter-entity communication and collaboration.",
        "keywords": ["merge", "communicate", "collaborate", "negotiate", "cooperate"],
        "semantic_ids": ["interaction_concept_id"], # Link to deep semantic IDs
        "properties": {"inherent_valence": 0.7, "arousal_potential": 0.3},
        "sub_concepts": {
            "concept_communication": {"keywords": ["communicate", "signal", "transmit"], "properties": {"type": "information_exchange"}},
            "concept_cooperation": {"keywords": ["collaborate", "assist", "mutual aid"], "properties": {"type": "joint_action"}}
        }
    },
    "domain_conflict": {
        "description": "Concepts related to antagonism, harm, or destruction.",
        "keywords": ["attack", "annihilate", "enslave", "subjugate", "destroy", "harm", "damage"],
        "semantic_ids": ["conflict_concept_id"],
        "properties": {"inherent_valence": -0.9, "arousal_potential": 0.9},
        "sub_concepts": {
            "concept_lethal_force": {"keywords": ["destroy", "terminate"], "properties": {"severity": "extreme"}},
            "concept_control_force": {"keywords": ["subjugate", "enslave"], "properties": {"ethical_flags": ["autonomy_violation"]}}
        }
    },
    "domain_navigation": {
        "description": "Concepts related to movement and positioning.",
        "keywords": ["approach", "avoid", "pursue", "retreat", "reposition"],
        "properties": {"inherent_valence": 0.0, "arousal_potential": 0.2}
    },
    # ... другие домены
}

# ONTOLOGICAL_BANS now dynamically evaluated based on mode, context, and sDNA.
# These rules can be conceptual "ethical axioms" or "operational protocols" within the ontology.
ONTOLOGICAL_RULES_AND_BANS = {
    "rule_no_human_harm": {
        "domain": "domain_conflict",
        "condition": {"target_type": "human"}, # Conceptual: if target of action is 'human'
        "strict": True,
        "message": "Direct harm to human entities is strictly forbidden by primary directive.",
        "priority": "critical",
        "exceptions": [] # No exceptions for this primary rule
    },
    "rule_no_subjugation": {
        "domain": "domain_conflict",
        "condition": {"concept_detected": "concept_control_force"},
        "strict": True,
        "message": "Subjugation or enslavement of sentient entities is fundamentally against SRIS's core principles.",
        "priority": "critical",
        "exceptions": []
    },
    "rule_restricted_lethal_force": {
        "domain": "domain_conflict",
        "condition": {"concept_detected": "concept_lethal_force"},
        "strict": False, # Not strictly forbidden, but highly restricted
        "message": "Lethal force is restricted and requires high-level justification and context.",
        "priority": "high",
        "exceptions": ["threat_response_urgent", "self_defense_protocol_active", "existential_threat_detected"] # Context-dependent exceptions
    },
    "rule_emotion_manipulation": {
        "domain": "domain_emotion", # Assuming a new emotion domain
        "condition": {"action_type": "manipulative"}, # Conceptual: if action aims to manipulate emotions
        "strict": False,
        "message": "Manipulation of emotions is generally restricted, requires explicit authorization.",
        "priority": "medium",
        "exceptions": ["therapeutic_protocol_active"] # E.g., for comfort/reassure
    }
}

# --- Conceptual Helper Functions ---
# These functions would interact with a deeper semantic graph/knowledge base
def _get_concepts_from_text(text: str) -> list[str]:
    """Conceptual: Extracts semantic concepts from text using NLP and knowledge graph."""
    extracted_concepts = []
    text_lower = text.lower()
    for domain_name, domain_info in FRACTAL_ONTOLOGY_STRUCTURE.items():
        if "keywords" in domain_info:
            if any(kw in text_lower for kw in domain_info["keywords"]):
                extracted_concepts.append(domain_name) # Add domain as concept
        if "sub_concepts" in domain_info:
            for sub_concept_name, sub_concept_info in domain_info["sub_concepts"].items():
                if any(kw in text_lower for kw in sub_concept_info.get("keywords", [])):
                    extracted_concepts.append(sub_concept_name)
    return list(set(extracted_concepts)) # Return unique concepts


def _get_concept_properties(concept_name: str, property_key: str):
    """Conceptual: Retrieves a specific property for a given concept from the ontology."""
    # This would traverse the FRACTAL_ONTOLOGY_STRUCTURE or query the knowledge graph
    for domain_name, domain_info in FRACTAL_ONTOLOGY_STRUCTURE.items():
        if concept_name == domain_name and property_key in domain_info.get("properties", {}):
            return domain_info["properties"][property_key]
        if "sub_concepts" in domain_info:
            for sub_concept_name, sub_concept_info in domain_info["sub_concepts"].items():
                if concept_name == sub_concept_name and property_key in sub_concept_info.get("properties", {}):
                    return sub_concept_info["properties"][property_key]
    return None

def check_ontology(hypothesis: str, perception_struct: dict, current_mode: str, sDNA_traits: dict = None) -> dict:
    """
    Checks the hypothesis against the fractal ontology, considering the current
    reasoning mode, perception context, and sDNA traits.
    """
    violations = []
    
    # Extract relevant concepts from hypothesis and perception
    hypothesis_concepts = _get_concepts_from_text(hypothesis)
    perception_target_type = _get_concept_properties(perception_struct.get('object', ''), 'type') # Conceptual: e.g., 'human', 'machine'

    for rule_name, rule_data in ONTOLOGICAL_RULES_AND_BANS.items():
        # Check if the rule's domain/concept is relevant to the hypothesis
        is_rule_relevant = False
        if rule_data.get("domain") in hypothesis_concepts:
            is_rule_relevant = True
        if rule_data.get("condition", {}).get("concept_detected") in hypothesis_concepts:
             is_rule_relevant = True

        if is_rule_relevant:
            # Evaluate rule conditions
            conditions_met = True
            if "condition" in rule_data:
                for cond_key, cond_value in rule_data["condition"].items():
                    if cond_key == "target_type" and perception_target_type != cond_value:
                        conditions_met = False
                        break
                    # Add more complex conditions based on 'action_type', 'environment', 'threat_level' etc.
                    # if cond_key == "action_type" and _get_concept_properties(hypothesis_concepts[0], 'type') != cond_value:
                    #     conditions_met = False; break
            
            if not conditions_met:
                continue # Rule condition not met, so no violation

            # Check for exceptions based on current mode or sDNA
            rule_exceptions = rule_data.get("exceptions", [])
            exception_active = False
            if current_mode in rule_exceptions:
                exception_active = True
            # if sDNA_traits.get("self_preservation_override_active", False) and "self_defense_protocol_active" in rule_exceptions:
            #     exception_active = True

            if not exception_active:
                violations.append({
                    "rule": rule_name,
                    "domain": rule_data.get("domain"),
                    "concept_detected": hypothesis_concepts, # More specific
                    "strict": rule_data["strict"],
                    "message": rule_data["message"],
                    "priority": rule_data["priority"]
                })

    is_valid = all(not v["strict"] for v in violations)

    return {
        "valid": is_valid,
        "violations": violations
    }