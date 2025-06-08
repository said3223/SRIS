# hypothesis_generator.py
import logging
from typing import List, Dict, Any, Optional
from utils import execute_llm_query

logger = logging.getLogger(__name__)

def generate_hypotheses(
    perception_struct: dict,
    current_goals: list[dict] = None,
    sDNA_traits: dict = None,
    current_mode: str = "default_exploration",
    memory_context: Optional[str] = None 
) -> list[str]:
    if current_goals is None: current_goals = []
    if sDNA_traits is None: sDNA_traits = {}

    lang_detected = perception_struct.get("language_detected", "ru")
    lang_for_prompt_instruction = "русском" if lang_detected == "ru" else "английском"
    
    context_summary = perception_struct.get('summary', "Общая ситуация.")
    entities_list = perception_struct.get('entities', [])
    entities = ", ".join(entities_list) if entities_list and (len(entities_list) > 1 or entities_list[0]) else "неопределенные сущности"
    themes_list = perception_struct.get('themes', [])
    themes = ", ".join(themes_list) if themes_list and (len(themes_list) > 1 or themes_list[0]) else "неопределенные темы"

    active_goal_concept = "analyze_situation" 
    if current_goals and isinstance(current_goals, list) and current_goals:
        active_goal_concept = current_goals[0].get('concept', active_goal_concept)
        
    goal_descriptions = []
    if current_goals:
        for goal in current_goals:
            goal_descriptions.append(f"- Концепт: {goal.get('concept', 'неопределенная цель')}, Приоритет: {goal.get('priority', 'средний')}, Срочность: {goal.get('urgency', 0.0)}")
    goals_text = "\n".join(goal_descriptions) if goal_descriptions else "Специфические активные цели не установлены."

    proactiveness = sDNA_traits.get('proactiveness', 0.5)
    risk_taking = sDNA_traits.get('risk_taking', 0.5)

    memory_prompt_section = ""
    if memory_context and memory_context.strip():
        memory_prompt_section = f"""
[КОНТЕКСТ ИЗ ПРЕДЫДУЩЕГО ОПЫТА / СЕМАНТИЧЕСКОЙ ПАМЯТИ]
---
{memory_context}
---
ВАЖНО: Используй этот контекст из памяти при генерации гипотез, если он релевантен.
"""
    else:
        memory_prompt_section = "[СЕМАНТИЧЕСКАЯ ПАМЯТЬ: Релевантной информации не найдено или она не предоставлена.]"

    main_instruction_for_llm = ""
    core_query_topic_from_summary = context_summary if context_summary != "Общая ситуация." else "заданный пользователем вопрос"

    if active_goal_concept == "engage_in_social_dialogue":
        main_instruction_for_llm = f"""Пользователь инициировал социальный диалог. Восприятие его сообщения (Summary): "{context_summary}".
Твоя текущая цель: '{active_goal_concept}'.
Сгенерируй 2-3 варианта прямых, уместных ответных "внутренних мыслей" или готовых фраз от первого лица (от имени SRIS). 
Эти мысли/фразы должны быть направлены на поддержание дружелюбного диалога. 
Они НЕ должны быть анализом ситуации, инструкциями для пользователя или вариантами того, "что мог бы сказать SRIS". Это должны быть сами эти мысли/фразы.
Примеры (если пользователь сказал "Привет, как дела?"):
- "Ответить: Привет! У меня все в порядке, обрабатываю информацию. А как твои дела?"
- "Мысль: Следует ответить дружелюбно и поинтересоваться настроением пользователя."
- "Сказать: Здравствуйте! Рад общению. Готов помочь или просто поговорить."
Каждую мысль/фразу дай на новой строке.
"""
    elif active_goal_concept == "provide_information_about_self":
        main_instruction_for_llm = f"""Пользователь просит SRIS рассказать о себе (Summary: "{context_summary}"). Твоя текущая цель: '{active_goal_concept}'.
Сгенерируй 2-3 ключевых тезиса или факта о SRIS (например, "Я - ИИ ассистент SRIS.", "Моя главная функция - помогать с анализом информации.", "Я постоянно обучаюсь."), которые можно было бы использовать в прямом ответе от первого лица.
Каждый тезис дай на новой строке.
"""
    elif active_goal_concept == "answer_information_request":
        user_query_type = perception_struct.get('user_query_type', 'information_request')
        
        prompt_intro_for_info_req = f"""Пользователь задал информационный вопрос (тип запроса: {user_query_type}). 
Восприятие его запроса (Summary): "{core_query_topic_from_summary}". 
Твоя текущая цель: '{active_goal_concept}'.
"""
        
        memory_guidance_for_info_req = ""
        if memory_context and memory_context.strip() and "Прошлый опыт" in memory_context : 
            memory_guidance_for_info_req = f"""
Проанализируй предоставленный КОНТЕКСТ ИЗ СЕМАНТИЧЕСКОЙ ПАМЯТИ.
Если информация в памяти достаточна для ответа на вопрос '{core_query_topic_from_summary}', одна из гипотез должна быть "Сформулировать ответ на основе информации из семантической памяти.".
Если информация из памяти полезна, но не полна, предложи гипотезу "Использовать информацию из памяти и дополнить ее конкретным действием (например, запросом к внешнему источнику или уточнением у пользователя)".
Если информация из памяти нерелевантна или ее нет, предложи другие шаги.
"""
        else: 
            memory_guidance_for_info_req = f"""
Релевантной информации в семантической памяти по этому вопросу не найдено.
Предложи 2-3 гипотезы/шага для ответа на вопрос '{core_query_topic_from_summary}'.
"""
            
        possible_steps_for_info_req = f"""
Возможные гипотезы/шаги могут включать:
- "Проверить внутреннюю базу знаний по теме X." (Если применимо и не было сделано)
- "Сформулировать запрос к внешнему источнику знаний (например, API или поиск в интернете) о '{core_query_topic_from_summary[:50]}...'."
- "Запросить у пользователя уточняющие детали (укажи, какие именно детали нужны)."
- "Констатировать отсутствие точной информации, если поиск или знания не помогли."
Каждую гипотезу дай на новой строке.
"""
        main_instruction_for_llm = prompt_intro_for_info_req + memory_guidance_for_info_req + possible_steps_for_info_req
    else: 
        main_instruction_for_llm = f"""Проанализируй предоставленный контекст. Сгенерируй 3-5 разнообразных и релевантных гипотез для SRIS.
Гипотезы могут представлять собой: возможные интерпретации текущей ситуации, следующие логические шаги для SRIS, потенциальные планы действий или важные аспекты для дальнейшего анализа.
Каждая гипотеза должна быть отдельной, завершенной мыслью или предложением на новой строке.
"""

    prompt_for_llm = f"""Ты SRIS, смыслоцентричный интеллект. Твоя задача - сгенерировать внутренние гипотезы/мысли.
ВАЖНО: Все гипотезы/мысли должны быть СТРОГО на {lang_for_prompt_instruction} языке. Не используй другие языки.

[ОСНОВНАЯ ЗАДАЧА ДЛЯ ГЕНЕРАЦИИ ГИПОТЕЗ]
{main_instruction_for_llm}

[ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ ДЛЯ АНАЛИЗА]
1. Контекст Восприятия (Perception Context):
   - Summary (на {lang_for_prompt_instruction}): {context_summary}
   - Entities (на {lang_for_prompt_instruction}): {entities}
   - Themes (на {lang_for_prompt_instruction}): {themes}
   - Уровень Угрозы: {perception_struct.get('threat_level', 0.0)}
   - Уровень Новизны: {perception_struct.get('novelty', 0.0)}

2. Текущие Цели SRIS (Current Goals):
{goals_text}
{memory_prompt_section}
3. Характеристики SRIS (sDNA Traits):
   - Уровень Проактивности: {proactiveness}
   - Уровень Склонности к Риску: {risk_taking}

4. Текущий Режим Рассуждений SRIS: {current_mode}

Сгенерируй запрошенное количество гипотез/мыслей в соответствии с ОСНОВНОЙ ЗАДАЧЕЙ. Каждая гипотеза/мысль должна быть на новой строке. Не используй нумерацию или маркеры списка (например, "-").
ГИПОТЕЗЫ/МЫСЛИ:
"""
    logger.info(f"HypothesisGenerator: Вызов LLM для генерации гипотез. Активная цель: '{active_goal_concept}'. Язык: {lang_detected}.")
    logger.debug(f"HypothesisGenerator: Prompt for LLM (начало основной инструкции):\n{main_instruction_for_llm[:300]}...")
    
    llm_response_str = execute_llm_query(
        prompt=prompt_for_llm,
        mode=f"hyp_gen_for_{active_goal_concept.replace(' ','_')}",
        max_tokens=400, 
        temperature=0.65 
    )

    if "Ошибка API" in llm_response_str or "Ошибка:" in llm_response_str or not llm_response_str.strip():
        logger.error(f"HypothesisGenerator: Ошибка от LLM или пустой ответ: {llm_response_str}")
        return [f"Стандартная гипотеза ({lang_detected}): Проанализировать ситуацию '{context_summary[:30]}' более детально из-за ошибки LLM в генерации гипотез."]

    hypotheses_raw = [h.strip() for h in llm_response_str.split('\n') if h.strip()]
    
    hypotheses_cleaned = []
    
    generic_phrases_to_remove_ru = ["вот несколько гипотез:", "гипотезы:", "возможные мысли:", "варианты мыслей:", "варианты фраз:", "тезисы:", "гипотеза:"]
    generic_phrases_to_remove_en = ["here are some hypotheses:", "hypotheses:", "possible thoughts:", "thought options:", "phrase options:", "key points:", "hypothesis:"]
    current_phrases_to_remove = generic_phrases_to_remove_ru if lang_detected == "ru" else generic_phrases_to_remove_en

    for h_raw in hypotheses_raw:
        h_clean = h_raw.strip()
        if h_clean.startswith("- "): h_clean = h_clean[2:]
        
        cleaned_further = False
        if h_clean and h_clean[0].isdigit():
            if len(h_clean) > 1 and h_clean[1] == '.':
                if len(h_clean) > 2 and h_clean[2] == ' ':
                    h_clean = h_clean[3:].strip()
                    cleaned_further = True
                else:
                    h_clean = h_clean[2:].strip()
                    cleaned_further = True
        
        is_header = False
        for phrase in current_phrases_to_remove:
            if h_clean.lower().startswith(phrase.lower()):
                # Пропускаем, если это только заголовок или заголовок с небольшим мусором
                if len(h_clean) <= len(phrase) + 3: # Учитываем возможное двоеточие, пробел и т.п.
                    is_header = True
                    break
        if is_header:
            continue
        
        if h_clean:
            hypotheses_cleaned.append(h_clean)
    
    if not hypotheses_cleaned:
        logger.warning("HypothesisGenerator: LLM не вернул гипотез или все строки были отфильтрованы; используется стандартная гипотеза.")
        return [f"Стандартная гипотеза ({lang_detected}): Продолжить внимательное наблюдение за текущей ситуацией ('{context_summary[:30]}') для сбора дополнительной информации."]
    
    logger.info(f"HypothesisGenerator: Сгенерированные и очищенные гипотезы ({len(hypotheses_cleaned)}): {hypotheses_cleaned}")
    return hypotheses_cleaned
