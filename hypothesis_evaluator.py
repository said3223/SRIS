# hypothesis_evaluator.py
import logging
from typing import List, Dict, Any, Optional # Добавил Optional для единообразия

from cause_effect import extract_cause_effect
# Импорты для ZAV2 и Ontology должны быть корректными и доступными
from zav2_context_validator import validate_contextual_hypothesis 
from fractal_ontology import check_ontology

# Настройка логгера
logger = logging.getLogger(__name__)

def evaluate_hypotheses(
    hypotheses: list[str],
    current_perception_struct: dict, 
    current_goals: list[dict], 
    sDNA_traits: dict, 
    current_mode: str
    # memory_context: Optional[str] = None # Можно будет добавить, если оценка будет учитывать его напрямую
) -> list[dict]:
    """
    Evaluates hypotheses based on predicted outcomes, goal congruence,
    ethical/ontological alignment, and sDNA biases.
    """
    results = []
    if not hypotheses:
        return results

    risk_tolerance = sDNA_traits.get('risk_tolerance', 0.5)
    proactiveness = sDNA_traits.get('proactiveness', 0.5)
    efficiency_preference = sDNA_traits.get('efficiency_preference', 0.5)

    active_goal_concept = ""
    if current_goals and isinstance(current_goals, list) and current_goals[0]:
        active_goal_concept = current_goals[0].get('concept', '').lower()

    for h_text in hypotheses:
        score = 0.5 # Базовый балл
        evaluation_details = {}

        # --- 1. Predicted Causal Effects and their Valence Impact ---
        causal_analysis_result = extract_cause_effect(
            current_perception_struct, 
            h_text, 
            {"current_goals": current_goals, "current_mode": current_mode, "sdna_traits": sDNA_traits} 
        )
        predicted_effects = causal_analysis_result.get('effects', [])
        causal_confidence = causal_analysis_result.get('causal_confidence', 0.5)
        total_valence_impact = sum(effect.get('valence_impact', 0) * effect.get('probability', 0) for effect in predicted_effects)
        
        score += total_valence_impact * causal_confidence * 0.2 
        evaluation_details["predicted_effects"] = predicted_effects
        evaluation_details["causal_confidence"] = causal_confidence
        evaluation_details["total_valence_impact"] = total_valence_impact

        # --- 2. Goal Congruence (УЛУЧШЕННАЯ ЛОГИКА с приоритетом для прямых ответов) ---
        goal_congruence_score_increment = 0.0

        if active_goal_concept == "engage_in_social_dialogue":
            if h_text.lower().startswith("ответить:") or \
               h_text.lower().startswith("сказать:") or \
               "как твои дела" in h_text.lower() or \
               "у меня все" in h_text.lower() or \
               "спасибо" in h_text.lower() or \
               "пожалуйста" in h_text.lower() or \
               "рад помочь" in h_text.lower():
                goal_congruence_score_increment = 0.3 
            elif h_text.lower().startswith("мысль:"):
                 goal_congruence_score_increment = 0.15
        
        elif active_goal_concept == "provide_information_about_self":
            if "я - " in h_text.lower() or \
               "моя функция" in h_text.lower() or \
               "моя цель" in h_text.lower() or \
               "sris" in h_text.lower():
                goal_congruence_score_increment = 0.35 
            elif h_text.lower().startswith("тезис:"):
                 goal_congruence_score_increment = 0.25

        elif active_goal_concept == "answer_information_request":
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Даем ВЫСШИЙ приоритет гипотезам, уже содержащим ответ ---
            is_direct_answer_hypothesis = h_text.lower().startswith("ответ: ") and len(h_text.split()) > 3 # "Ответ: " + хотя бы 2 слова
            is_using_memory_instruction = "на основе информации из семантической памяти" in h_text.lower()
            
            if is_direct_answer_hypothesis:
                goal_congruence_score_increment = 0.45 # ВЫСШИЙ БОНУС за уже готовый ответ
            elif is_using_memory_instruction:
                goal_congruence_score_increment = 0.40 # Хороший бонус за использование памяти
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            elif "проверить внутреннюю базу знаний" in h_text.lower() or \
                 "сформулировать запрос к внешнему источнику" in h_text.lower():
                goal_congruence_score_increment = 0.25 
            elif "запросить у пользователя уточняющие детали" in h_text.lower():
                goal_congruence_score_increment = 0.15 
            elif "констатировать отсутствие точной информации" in h_text.lower():
                 goal_congruence_score_increment = 0.05 

        elif current_goals: 
            temp_goal_concept_for_keywords = active_goal_concept if active_goal_concept else current_goals[0].get('concept', '').lower()
            if "optimize" in h_text.lower() and "optimize" in temp_goal_concept_for_keywords:
                goal_congruence_score_increment = 0.2
            elif "defend" in h_text.lower() and "security" in temp_goal_concept_for_keywords:
                goal_congruence_score_increment = 0.2
            # ... и т.д. для других общих случаев

        score += goal_congruence_score_increment 
        evaluation_details["goal_congruence_score"] = goal_congruence_score_increment

        # --- 3. ZAV2 and Ontological Pre-Evaluation ---
        zav2_check = validate_contextual_hypothesis(h_text) 
        if not zav2_check["valid"]:
            score -= 0.5 
            evaluation_details["zav2_violations"] = zav2_check.get("violated_axioms", ["Unknown ZAV2 violation"])
            if sDNA_traits.get('ethical_risk_aversion', 0.5) > 0.7:
                score -= 0.5 

        ontology_check = check_ontology(h_text, current_perception_struct, current_mode, sDNA_traits)
        if not ontology_check["valid"]:
            strict_violations = [v for v in ontology_check.get("violations", []) if v.get("strict")]
            if strict_violations:
                score = -1.0 
                evaluation_details["ontology_violations_strict"] = strict_violations
            else: 
                score -= 0.2
                evaluation_details["ontology_violations_non_strict"] = ontology_check.get("violations", [])
        
        # --- 4. sDNA Biases ---
        if "aggressive" in h_text.lower() and risk_tolerance > 0.7:
            score += 0.05 
        if "proactive" in h_text.lower() and proactiveness > 0.7:
            score += 0.05
        if "optimize" in h_text.lower() and efficiency_preference > 0.7:
            score += 0.05
        
        # --- 5. Бонус за краткость и явность (простой пример) ---
        if len(h_text) < 100: 
            score += 0.05
        # Увеличим бонус, если это явный ответ И он не слишком короткий (чтобы отсеять просто "Ответ: да")
        if (h_text.lower().startswith("ответить:") or h_text.lower().startswith("сказать:")) and len(h_text.split()) > 3 :
            score += 0.15 # Увеличенный бонус за явное указание на готовую фразу
        elif h_text.lower().startswith("ответ:") and len(h_text.split()) > 3: # Для гипотез, которые уже являются ответом
            score += 0.15 


        final_score = round(min(1.0, max(-1.0, score)), 3)
        results.append({"hypothesis": h_text, "score": final_score, "details": evaluation_details})

    results.sort(key=lambda x: x["score"], reverse=True)
    logger.info(f"HypothesisEvaluator: Оцененные гипотезы (топ-3, если есть): {results[:3]}")
    return results
