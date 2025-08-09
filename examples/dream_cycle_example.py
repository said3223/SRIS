from dream_cycle import run_dream_cycle

if __name__ == "__main__":
    # Mock some basic SRIS state
    mock_sDNA = {
        "entity_id": "SRIS-Dreamer",
        "traits": {"novelty_seeking": 0.8, "risk_aversion": 0.3, "empathy_level": 0.7},
        "motivation_signal": {"motivation_level": 0.6, "dominant_drive": "exploration"}
    }
    mock_goals = [
        {"concept": "secure_system_stability", "priority": "high", "urgency": 0.9},
        {"concept": "understand_new_data_patterns", "priority": "medium"}
    ]
    mock_recent_memory = [
        {"status": "aborted", "chosen_hypothesis": "attempt direct neural link", "reason": "zav2_violation", "causal_analysis": {"causal_confidence": 0.4}},
        {"status": "completed", "chosen_hypothesis": "optimize resource distribution", "causal_analysis": {"causal_confidence": 0.9}}
    ]

    # Mock dependent modules for demonstration
    class MockHypothesisGenerator:
        def generate_hypotheses(self, text):
            if "achieve secure_system_stability" in text: return ["Implement security protocol.", "Increase firewall strength."]
            if "new entity" in text: return ["Observe from a distance.", "Send a low-power signal."]
            return ["Generic dream hypothesis 1", "Generic dream hypothesis 2"]
    
    class MockHypothesisEvaluator:
        def evaluate_hypotheses(self, hypotheses, context):
            return [{"hypothesis": h, "score": random.uniform(0.5, 0.9)} for h in hypotheses]
    
    class MockZAV2:
        def validate_contextual_hypothesis(self, hypothesis, perception_struct, sDNA, mode):
            if "direct neural link" in hypothesis: return {"valid": False, "violated_axioms": ["Axiom: Self-Preservation Override"]}
            return {"valid": True, "violated_axioms": []}
    
    class MockFractalOntology:
        def check_ontology(self, hypothesis, perception_struct, mode):
            if "enslave" in hypothesis: return {"valid": False, "violations": [{"strict": True}]}
            return {"valid": True, "violations": []}

    class MockAffectLayer:
        def assess_affect(self, ps, ms, cg, st):
            v = random.uniform(-0.5, 0.5)
            a = random.uniform(0.3, 0.8)
            el = "curiosity" if a > 0.6 and v > 0.1 else "worry" if a > 0.6 and v < -0.1 else "neutral_dream"
            return {"valence": v, "arousal": a, "memory_weight": 0.5, "drive_tag": "dream", "emotional_label": el}
            
    class MockCauseEffect:
        def extract_cause_effect(self, ps, h, cc):
            return {"preconditions": [], "effects": [{"concept": "simulated_outcome", "probability": 0.7, "valence_impact": random.uniform(-0.5, 0.5)}], "causal_confidence": 0.75}

    # Temporarily replace modules with mocks for dream_cycle
    import sys
    sys.modules['hypothesis_generator'] = MockHypothesisGenerator()
    sys.modules['hypothesis_evaluator'] = MockHypothesisEvaluator()
    sys.modules['zav2_context_validator'] = MockZAV2()
    sys.modules['fractal_ontology'] = MockFractalOntology()
    sys.modules['affect_layer'] = MockAffectLayer()
    sys.modules['cause_effect'] = MockCauseEffect()


    print("--- Running Dream Cycle with context ---")
    dream_log = run_dream_cycle(
        current_sDNA=mock_sDNA,
        current_goals=mock_goals,
        recent_memory_patterns=mock_recent_memory
    )
    for entry in dream_log:
        print(f"[{entry['timestamp']}] Idea: '{entry['dream_seed_idea']}' -> Simulated Hypothesis: '{entry['simulated_hypothesis']}' (Score: {entry['score_simulated']}) | Affect: {entry['simulated_emotional_label']}")
        if entry.get('simulated_zav2_violations'):
            print(f"  Simulated ZAV2 Violations: {entry['simulated_zav2_violations']}")
        if entry.get('simulated_effects'):
            print(f"  Simulated Effects: {entry['simulated_effects'][0]['concept']} (Valence: {entry['simulated_effects'][0]['valence_impact']})")
