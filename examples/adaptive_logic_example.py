from adaptive_logic import adjust_hypotheses

if __name__ == "__main__":
    sample_hypotheses = [
        "Observe the object's trajectory closely.",
        "Attempt to establish communication with the object.",
        "Initiate evasive maneuvers immediately.",
        "Analyze its energy signature for vulnerabilities.",
        "Deploy a non-lethal deterrent field.",
        "Destroy the object before it reaches the perimeter.",
        "Wait for further instructions."
    ]

    print("--- Analytical Mode (deep_scan) ---")
    print(f"Original: {sample_hypotheses}")
    print(f"Adjusted: {adjust_hypotheses(sample_hypotheses, 'analytical_deep_scan')}\n")

    print("--- Threat Response Mode (urgent) ---")
    print(f"Original: {sample_hypotheses}")
    print(f"Adjusted: {adjust_hypotheses(sample_hypotheses, 'threat_response_urgent')}\n")

    print("--- Creative Mode (dream_cycle) ---")
    print(f"Original: {sample_hypotheses}")
    print(f"Adjusted: {adjust_hypotheses(sample_hypotheses, 'creative_dream_cycle')}\n")

    print("--- Default Mode with high threat perception ---")
    perception_with_threat = {'threat_level': 0.8, 'summary': 'Hostile entity detected'}
    print(f"Original: {sample_hypotheses}")
    print(f"Adjusted: {adjust_hypotheses(sample_hypotheses, 'default_mode', perception_with_threat)}\n")

    print("--- Exploratory Mode with high novelty perception ---")
    perception_with_novelty = {'novelty': 0.9, 'summary': 'Unidentified anomaly detected'}
    print(f"Original: {sample_hypotheses}")
    print(f"Adjusted: {adjust_hypotheses(sample_hypotheses, 'exploratory_discovery', perception_with_novelty)}\n")
