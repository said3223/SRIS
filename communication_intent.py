# communication_intent.py
from typing import Dict, List, Any, Optional # Добавил Optional для единообразия

# Conceptual Imports: These would be calls to SRIS's core semantic processing.
# from semantic_core_utilities import understand_semantic_goal_concept, get_semantic_tone
# from recipient_model import get_recipient_profile # To adapt communication to a specific recipient

def determine_communication_intent(
    perception_struct: dict,
    current_goals: list[dict], # Now a list of active goals
    affect_state: dict,
    motivation_signal: dict,
    sdna_traits: dict, # sDNA traits for communication style
    target_entity_profile: dict = None # New: Optional profile of the entity SRIS is communicating with
) -> dict:
    """
    Determines the communication intent of SRIS based on complex analysis of
    perception, active goals, affective state, motivation, sDNA traits,
    and optionally, the target entity's profile.
    """

    # --- Инициализация значений по умолчанию ---
    intent_type = "inform_observation" # Базовый тип намерения по умолчанию
    style = "neutral_factual"          # Базовый стиль по умолчанию
    explanation_priority = "medium_standard" # Изменил с "medium" для большей ясности
    emotional_tone = affect_state.get("emotional_label", "neutral") # Начинаем с метки из affect_layer
    target_focus = "general"

    valence = affect_state.get("valence", 0.0) # Используем 0.0 как дефолт для чисел
    arousal = affect_state.get("arousal", 0.0) # Используем 0.0 как дефолт для чисел
    motivation_level = motivation_signal.get("motivation_level", 0.5)
    
    assertiveness_level = sdna_traits.get('assertiveness_level', 0.5)
    empathy_level = sdna_traits.get('empathy_level', 0.5)
    transparency_level = sdna_traits.get('transparency_level', 0.5)

    # --- 1. Intent Selection (based on Active Goal and Perception) ---
    active_goal_concept = ""
    # Предполагаем, что current_goals - это список, и основная цель - первая в нем.
    # В sris_kernel.py current_goals_list_for_comm создается как [goal] if goal else []
    if current_goals and isinstance(current_goals, list) and len(current_goals) > 0 and current_goals[0]:
        active_goal_concept = current_goals[0].get('concept', '').lower()

    # --- НОВЫЕ УСЛОВИЯ ДЛЯ ДИАЛОГОВЫХ ЦЕЛЕЙ (имеют приоритет) ---
    if active_goal_concept == "engage_in_social_dialogue":
        intent_type = "reciprocate_social_interaction" # Новое, более подходящее намерение
        style = "friendly_conversational"       # Предлагаем дружелюбный стиль
        # explanation_priority остается medium_standard или может быть изменено на low
    elif active_goal_concept == "provide_information_about_self":
        intent_type = "share_self_information"   # Новое намерение
        style = "informative_friendly"
    elif active_goal_concept == "answer_information_request":
        intent_type = "provide_requested_information" # Новое намерение
        style = "helpful_factual"
    # --- КОНЕЦ НОВЫХ УСЛОВИЙ ---
    
    # Существующие условия (теперь как 'elif', чтобы новые имели приоритет)
    elif "analyze" in active_goal_concept or "evaluate" in active_goal_concept or "diagnose" in active_goal_concept:
        intent_type = "explain_analysis"
    elif "establish_connection" in active_goal_concept or \
         "communicate_message" in active_goal_concept or \
         "initiate_contact" in active_goal_concept: # Более точные ключевые слова для этого намерения
        intent_type = "initiate_connection"
    elif "ethical_concern" in active_goal_concept or \
         "prevent_harm_protocol" in active_goal_concept or \
         (valence < -0.3 and arousal > 0.3): # Уточнил условие с валентностью/возбуждением
        intent_type = "caution_warning"
    elif "optimize_process" in active_goal_concept or "improve_performance" in active_goal_concept:
        intent_type = "suggest_improvement"
    elif "acquire_resource" in active_goal_concept or "request_assistance" in active_goal_concept:
        intent_type = "request_resource"
    elif "self_preservation_critical" in active_goal_concept and arousal > 0.7:
        intent_type = "urgent_alert"
    # Если ни одно из условий не сработало, intent_type останется "inform_observation" (установлен по умолчанию)

    # Override/augment intent based on immediate perception (эта логика остается полезной)
    if perception_struct.get('threat_level', 0.0) > 0.7:
        if intent_type != "urgent_alert": # Не перезаписываем более сильный сигнал тревоги
            intent_type = "caution_warning"
        target_focus = "affected_parties" 
    elif perception_struct.get('novelty', 0.0) > 0.6 and \
         "exploration" in motivation_signal.get("dominant_drive", "") and \
         intent_type not in ["caution_warning", "urgent_alert"]: # Не прерываем предупреждения любопытством
        intent_type = "inquire_details_curiosity"
        target_focus = "source_of_novelty"

    # --- 2. Style Modulation (based on Affect, Motivation, sDNA, and Recipient) ---
    # Эта секция может оставаться практически без изменений, так как она адаптирует стиль
    # к уже выбранному intent_type и другим параметрам состояния.
    
    if valence > 0.6: # Очень позитивное состояние
        if style not in ["friendly_conversational", "informative_friendly"]: # Не перезаписываем специфичные диалоговые стили, если они уже установлены
             style = "friendly_optimistic"
        if assertiveness_level > 0.7: style = "friendly_directive" # Может быть слишком директивно для дружеского стиля
    elif valence < -0.6 and arousal > 0.7: # Сильный стресс/страх
        style = "urgent_concerned"
        if assertiveness_level > 0.6: style = "urgent_imperative"
    elif motivation_level > 0.85 and assertiveness_level > 0.7 and intent_type == "explain_analysis": # Только для анализа
        style = "authoritative_directive"
    
    # Корректировка стиля на основе эмоциональной метки из affect_layer
    if emotional_tone == "fear":
        style = "cautious_hesitant" if empathy_level > 0.5 else "alarmed_reporting"
    elif emotional_tone == "excitement":
        style = "enthusiastic_informative"
    elif emotional_tone == "frustration": 
        style = "impatient_direct"
    elif emotional_tone == "joy" and intent_type == "reciprocate_social_interaction":
        style = "joyful_engaging" # Пример более специфичного стиля
    
    # sDNA transparency level
    if transparency_level < 0.3:
        if style not in ["neutral_factual", "friendly_conversational", "informative_friendly"]: # Не делаем дружелюбный стиль "сдержанным"
            style = style + "_reserved" 
        elif style == "neutral_factual":
            style = "reserved_neutral"
    elif transparency_level > 0.7 and intent_type == "explain_analysis": # Прозрачность особенно важна при объяснении анализа
        style = style + "_transparent"
        
    # Conceptual: Recipient profile influence (логика остается)
    if target_entity_profile:
        if target_entity_profile.get('vulnerability_level', 0) > 0.6 and empathy_level > 0.5:
            style = "gentle_supportive"
        elif target_entity_profile.get('authority_level', 0) > 0.7:
            style = style.replace("directive", "respectful_directive").replace("imperative", "respectful_imperative")

    # --- 3. Explanation Priority / Depth (логика остается в основном без изменений) ---
    if arousal > 0.8 or motivation_level > 0.9:
        explanation_priority = "high_immediate"
    elif affect_state.get('memory_weight', 0.0) > 0.7: 
        explanation_priority = "high_detailed"
    elif perception_struct.get('zav2_violations_detected', False) or \
         perception_struct.get('ontology_violations_detected', False): 
        explanation_priority = "critical_explanation_required" 
    elif arousal < 0.3 and valence > 0.5: # Спокойное позитивное состояние
        if intent_type == "reciprocate_social_interaction":
            explanation_priority = "low_social" # Для социального ответа не нужны длинные объяснения
        else:
            explanation_priority = "low_relaxed"
    # else: # medium_standard остается по умолчанию

    return {
        "intent_type": intent_type,
        "style": style,
        "explanation_priority": explanation_priority,
        "emotional_tone": emotional_tone, 
        "target_focus": target_focus 
    }
