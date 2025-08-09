from ml_nae_core import (
    ScenarioReasoningEngine,
    MetaPredictiveSelector,
    ReflexPlanner,
    SRISNeuroActionEngine,
)

if __name__ == "__main__":
    # === Mockups ===
    def mock_execute_llm_query_for_sre(prompt: str, mode: str, max_tokens: int, temperature: float) -> str:
        logger.info(f"MOCK SRE LLM Query (mode: {mode}): Промпт получен, начинается с: '{prompt[:150]}...'")
        lang_for_response = "русском" # По умолчанию
        if "Language: en" in prompt or "языке: en" in prompt: # Очень грубая проверка
            lang_for_response = "английском"

        if lang_for_response == "русском":
            return """Scenario ID: SCN_001
Scenario Description: Пользователь выглядит озадаченным и ожидает дальнейших разъяснений.
Proposed SRIS Action: предложить_дополнительную_информацию_или_перефразировать_ответ
Action Confidence: 0.85
Action Justification: Прямое наблюдение за реакцией пользователя указывает на необходимость прояснения.
Predicted Effects Summary: Пользователь лучше поймет предыдущий ответ, диалог продолжится конструктивно.
Estimated Risk Level: низкий
---
Scenario ID: SCN_002
Scenario Description: Пользователь может быть не удовлетворен ответом и решить прекратить диалог.
Proposed SRIS Action: вежливо_завершить_текущую_тему_и_предложить_новую
Action Confidence: 0.60
Action Justification: Низкая вовлеченность пользователя может сигнализировать о потере интереса.
Predicted Effects Summary: Диалог может быть сохранен переключением на интересную пользователю тему.
Estimated Risk Level: средний
"""
        else: # English example
            return """Scenario ID: SCN_001
Scenario Description: User appears confused and awaits further clarification.
Proposed SRIS Action: offer_additional_information_or_rephrase_response
Action Confidence: 0.85
Action Justification: Direct observation of user's reaction indicates a need for clarity.
Predicted Effects Summary: User will better understand the previous response, dialogue will continue constructively.
Estimated Risk Level: low
"""
            
    # === SRISContext Example ===
    example_context_ru: SRISContext = {
        "perception": {"summary": "Пользователь выглядит озадаченным.", "threat_level": 0.1, "novelty": 0.2, "language_detected": "ru", "user_query_type": "feedback_statement", "entities": ["пользователь"], "themes": ["непонимание"]},
        "active_goal": {"concept": "ensure_user_understanding", "priority": "high", "urgency": 0.7, "goal_id": "g1"},
        "affect": {"valence": -0.2, "arousal": 0.4, "emotional_label": "concern", "memory_weight": 0.5, "drive_tag": "coherence"},
        "motivation": {"dominant_drive": "coherence", "motivation_level": 0.7},
        "sDNA_traits": {"proactiveness": 0.7, "risk_taking": 0.3, "ethics_sensitivity": 0.9, "curiosity_novelty_bias": 0.5, "self_preservation_priority": 0.8},
        "system_flags": {"zav2_violation_imminent": False}
    }
    
    example_context_critical_threat: SRISContext = {
         "perception": {"summary": "Обнаружена прямая физическая угроза целостности системы!", "threat_level": 0.95, "novelty": 0.8, "language_detected": "ru", "user_query_type": "system_alert"},
        "active_goal": {"concept": "self_preservation", "priority": "critical", "urgency": 1.0, "goal_id": "g_self"},
        "affect": {"valence": -0.9, "arousal": 0.95, "emotional_label": "fear"},
        "motivation": {"dominant_drive": "survival", "motivation_level": 1.0},
        "sDNA_traits": {"proactiveness": 0.9, "risk_taking": 0.6, "ethics_sensitivity": 0.5, "curiosity_novelty_bias": 0.2, "self_preservation_priority": 0.95},
        "system_flags": {"zav2_violation_imminent": False}
    }


    # === Initialization ===
    sre = ScenarioReasoningEngine(llm_func=mock_execute_llm_query_for_sre)
    mps = MetaPredictiveSelector(confidence_threshold=0.70) # Устанавливаем порог для MetaPredictor
    # Для ReflexPlanner можно передать пустой список правил, если дефолтные не нужны, или расширить их
    custom_rules = ReflexPlanner()._get_default_reflex_rules() # Берем дефолтные + можно добавить свои
    # custom_rules.append(my_another_custom_rule_function) 
    frm_plus = ReflexPlanner(reflex_rules=custom_rules)
    
    ml_nae = SRISNeuroActionEngine(scenario_engine=sre, metapredictor=mps, reflex_engine=frm_plus)

    # === Test Run 1: Normal situation ===
    logger.info("\n--- ML-NAE Test 1: Нормальная ситуация (озадаченный пользователь) ---")
    action1 = ml_nae.decide(example_context_ru)
    print(f"ML-NAE Решение 1: {action1}")

    # === Test Run 2: Critical Threat ===
    logger.info("\n--- ML-NAE Test 2: Критическая угроза (ожидаем рефлекс) ---")
    action2 = ml_nae.decide(example_context_critical_threat)
    print(f"ML-NAE Решение 2: {action2}")
    
    # === Test Run 3: ZAV2 flag ===
    example_context_zav2_violation = example_context_ru.copy() # Копируем нормальный контекст
    example_context_zav2_violation["system_flags"] = {"zav2_violation_imminent": True}
    logger.info("\n--- ML-NAE Test 3: Флаг нарушения ZAV2 (ожидаем рефлекс) ---")
    action3 = ml_nae.decide(example_context_zav2_violation)
    print(f"ML-NAE Решение 3: {action3}")

