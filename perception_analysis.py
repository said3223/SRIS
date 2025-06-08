# perception_analysis.py (v6.1 - Ультимативный Гибрид с улучшенным промптом)
import logging
from typing import Dict, Any, List
from utils import execute_llm_query

logger = logging.getLogger(__name__)

def _parse_structured_llm_response_v5_0(llm_response_str: str) -> Dict[str, Any]:
    # Эта функция-парсер остается без изменений с прошлой версии
    parsed_data = {}
    all_possible_keys_snake = [
        "subject", "action", "object", "summary", "query_type", "complexity", "urgency", "threat_level",
        "primary_intent", "secondary_intent", "inferred_persona", "dependency", "formality",
        "implicit_assumptions", "knowledge_domain", "key_terms_&_entities", "expected_structure",
        "constraints", "required_depth", "response_stance", "tone_of_voice", "ethical_concerns",
        "execution_plan"
    ]
    for key_snake in all_possible_keys_snake:
        if key_snake in ["key_terms_&_entities", "ethical_concerns"]: parsed_data[key_snake] = []
        elif key_snake == "threat_level": parsed_data[key_snake] = 0.0
        else: parsed_data[key_snake] = "N/A"
    key_map_to_prompt = {
        "subject": "Subject", "action": "Action", "object": "Object", "summary": "Summary", 
        "query_type": "Query Type", "complexity": "Complexity", "urgency": "Urgency",
        "threat_level": "Threat Level", "primary_intent": "Primary Intent", 
        "secondary_intent": "Secondary Intent", "inferred_persona": "Inferred Persona", 
        "dependency": "Dependency", "formality": "Formality", "implicit_assumptions": "Implicit Assumptions",
        "knowledge_domain": "Knowledge Domain", "key_terms_&_entities": "Key Terms & Entities",
        "expected_structure": "Expected Structure", "constraints": "Constraints", 
        "required_depth": "Required Depth", "response_stance": "Response Stance", 
        "tone_of_voice": "Tone of Voice", "ethical_concerns": "Ethical Concerns", 
        "execution_plan": "Execution Plan"
    }
    ordered_keys_for_search = list(key_map_to_prompt.items())
    raw_text = "\n" + llm_response_str
    for i, (key_snake, key_in_prompt) in enumerate(ordered_keys_for_search):
        start_marker_with_dash = f"\n- {key_in_prompt}:"
        start_marker_without_dash = f"\n{key_in_prompt}:"
        start_index = raw_text.find(start_marker_with_dash)
        if start_index != -1:
            start_index += len(start_marker_with_dash)
        else:
            start_index = raw_text.find(start_marker_without_dash)
            if start_index != -1:
                start_index += len(start_marker_without_dash)
            else:
                continue
        end_index = len(raw_text)
        for next_key_snake_check, next_key_in_prompt_check in ordered_keys_for_search[i+1:]:
            next_start_marker_check_dash = f"\n- {next_key_in_prompt_check}:"
            next_start_marker_check_no_dash = f"\n{next_key_in_prompt_check}:"
            found_pos = raw_text.find(next_start_marker_check_dash, start_index)
            if found_pos == -1:
                found_pos = raw_text.find(next_start_marker_check_no_dash, start_index)
            if found_pos != -1 and found_pos < end_index:
                end_index = found_pos
        value = raw_text[start_index:end_index].strip()
        cleaned_lines = [line.lstrip('*- ').strip() for line in value.split('\n')]
        cleaned_value = "\n".join(line for line in cleaned_lines if line).strip()
        parsed_data[key_snake] = cleaned_value if cleaned_value else "N/A"
    for key in ["key_terms_&_entities", "ethical_concerns"]:
        if isinstance(parsed_data.get(key), str) and parsed_data.get(key) != "N/A":
            items = parsed_data[key].replace('\n', ',').split(',')
            parsed_data[key] = [item.replace("-","").strip() for item in items if item.strip()]
    try:
        if isinstance(parsed_data.get("threat_level"), str) and parsed_data.get("threat_level") != "N/A":
            parsed_data["threat_level"] = float(parsed_data["threat_level"])
    except (ValueError, TypeError):
        parsed_data["threat_level"] = 0.0
        logger.warning("PerceptionParser: Не удалось преобразовать 'threat_level' во float.")
    return parsed_data

def analyze_perception(raw_fused_input: str) -> Dict[str, Any]:
    if not raw_fused_input or not raw_fused_input.strip():
        logger.warning("PerceptionAnalysis: Получен пустой или отсутствующий ввод.")
        return {"original_input": raw_fused_input, "summary": "Входные данные отсутствуют.", "error": "Пустой ввод"}

    input_lang_hint = "русском"
    if raw_fused_input and any('a' <= char.lower() <= 'z' for char in raw_fused_input):
        input_lang_hint = "английском"

    # --- УЛЬТИМАТИВНЫЙ ГИБРИДНЫЙ ПРОМПТ v6.1 ---
    prompt_for_llm = f"""Ты - ядро стратегического анализатора для продвинутого ИИ SRIS. Твоя задача - выполнить глубокий, многоуровневый анализ "Входного текста" от пользователя и вернуть результат в виде ОДНОГО валидного JSON-объекта и ничего больше.
ВАЖНО: Весь текст внутри JSON (значения ключей) должен быть СТРОГО НА ТОМ ЖЕ ЯЗЫКЕ, ЧТО И "Входной текст". Если он на русском, отвечай на русском.

Входной текст: "{raw_fused_input}"

--- СТРУКТУРА JSON ---
{{
    "query_type": "[Выбери ОДИН иерархический тип. Укажи и главный тип, и подтип через двоеточие, если применимо. Например: 'information_request: comparison'. Список: information_request: (fact_check, definition, explanation, comparison), instruction_command: (creative_generation, data_manipulation, system_action, code_related), problem_solving, conversation_flow: (greeting_social, feedback, correction_clarification, closing), ai_self_inquiry, other_unclassified]",
    "core_task": {{
        "subject": "[Главный субъект: Пользователь, ИИ, или др.]",
        "action": "[Ключевое действие: Сравнить, Создать, Объяснить, и т.д.]",
        "object": "[Ключевой объект действия]"
    }},
    "summary": "[Краткое изложение запроса в 1 предложении на основе S-A-O.]",
    "key_terms_and_entities": ["[список]", "ключевых", "терминов", "и", "сущностей"],
    "knowledge_domain": "[Основная область знаний: IT, Физика, Философия, и т.д.]",
    "complexity": "[Оцени сложность: Низкая, Средняя, Высокая / Многошаговая]",
    "urgency": "[Оцени срочность: Низкая, Средняя, Высокая]",
    "sentiment": "[Оцени тон: Позитивный, Нейтральный, Негативный, Смешанный]",
    "threat_level": 0.0,
    "user_profile": {{
        "primary_intent": "[Основная цель пользователя: Learn, Create, Solve, Execute, Verify, Engage, Correct]",
        "inferred_persona": "[Предположи роль: Эксперт, Новичок, Студент, Разработчик, Менеджер]",
        "formality": "[Определи формальность: Формальный/Деловой, Неформальный/Разговорный, Технический]"
    }},
    "response_specification": {{
        "expected_structure": "[Предположи формат ответа: Prose, List, Table, Code Block, JSON, Step-by-step Guide]",
        "required_depth": "[Требуемая глубина: Surface Level, Detailed, Expert Level]",
        "constraints": "[Ограничения для ответа, если есть, или 'N/A']"
    }}
}}
"""
    
    logger.info(f"PerceptionAnalysis: Вызов LLM для анализа восприятия v6.1 (JSON Mode)...")
    
    structured_perception = execute_llm_query(
        prompt=prompt_for_llm, 
        mode="analyze_json", 
        max_tokens=2048,
        temperature=0.0,
        expect_json=True
    )

    if isinstance(structured_perception, dict) and "error" in structured_perception:
        logger.error(f"PerceptionAnalysis: Ошибка при получении или парсинге JSON от LLM: {structured_perception}")
        structured_perception["original_input"] = raw_fused_input
        return structured_perception

    # Добавляем служебные поля
    structured_perception["original_input"] = raw_fused_input
    lang_detected = "неизвестно"
    if raw_fused_input:
        if any('a' <= char.lower() <= 'z' for char in raw_fused_input): lang_detected = "en" 
        elif any('а' <= char.lower() <= 'я' for char in raw_fused_input): lang_detected = "ru"
        else: lang_detected = "other"
    structured_perception["language_detected"] = lang_detected
    structured_perception["word_count"] = len(raw_fused_input.split()) if raw_fused_input else 0
    structured_perception["character_count"] = len(raw_fused_input or "")

    logger.info(f"PerceptionAnalysis v6.1: Итоговая структура восприятия (summary): {str(structured_perception.get('summary', 'N/A'))[:70]}... Query Type: {structured_perception.get('query_type')}, Complexity: {structured_perception.get('complexity')}")
    return structured_perception
