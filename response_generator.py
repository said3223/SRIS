# response_generator.py
import logging
from typing import Dict, Any

from utils import execute_llm_query

# Настройка логгера
logger = logging.getLogger(__name__)

def generate_sris_response(
    reasoning_chain: Dict[str, Any]
) -> str:
    comm_intent = reasoning_chain.get("communication_intent", {})
    perception = reasoning_chain.get("perception_struct", {})
    chosen_hypothesis_text = reasoning_chain.get("chosen_hypothesis", {}).get("hypothesis", "мои выводы не определены")
    affect = reasoning_chain.get("affect", {})
    
    # --- Определение языка для ответа ---
    # Извлекаем язык, определенный в perception_analysis
    # Устанавливаем русский как язык по умолчанию, если язык не определен или 'other'
    detected_lang = perception.get("language_detected", "ru") 
    
    response_language_instruction = ""
    if detected_lang == "ru":
        response_language_instruction = "Отвечай на русском языке."
    elif detected_lang == "en":
        response_language_instruction = "Respond in English."
    else: # Для 'other' или если язык не был определен, используем язык по умолчанию
        response_language_instruction = "Отвечай на русском языке." 
        # Или можно выбрать другой язык по умолчанию, например, английский:
        # response_language_instruction = "Respond in English."
    # --- Конец определения языка ---
        
    emotional_tone_label = affect.get("emotional_label", "нейтральное") 
    intent_type = comm_intent.get("intent_type", "inform_observation")
    style = comm_intent.get("style", "neutral_factual")
    
    perception_summary = perception.get("summary", "Нет данных для изложения.")
    goal_concept = reasoning_chain.get("goal", {}).get("concept", "анализ текущей ситуации")
    
    prompt = f"""Ты - продвинутый ИИ ассистент SRIS. Твоя задача - сформулировать естественный и полезный ответ пользователю.
{response_language_instruction}
Действуй строго в соответствии с заданными параметрами коммуникации.

Внутренний контекст SRIS:
- Анализ ситуации (восприятие): "{perception_summary}"
- Основная цель SRIS: "{goal_concept}"
- Выбранная гипотеза/основной вывод SRIS: "{chosen_hypothesis_text}"
- Эмоциональное состояние SRIS: "{emotional_tone_label}"

Параметры для твоего ответа:
- Тип намерения (Intent Type): "{intent_type}" 
- Стиль речи (Style): "{style}"

Инструкции по ответу в зависимости от типа намерения:
- Если "{intent_type}" это "explain_analysis" или "suggest_improvement": кратко и по существу изложи суть анализа или предложения, опираясь на "Выбранная гипотеза/основной вывод SRIS".
- Если "{intent_type}" это "caution_warning" или "urgent_alert": будь ясен, точен и сообщи о причине беспокойства.
- Если "{intent_type}" это "initiate_connection": будь дружелюбен и открой диалог.
- Если "{intent_type}" это "inquire_details_curiosity": задай вежливый уточняющий вопрос, чтобы получить больше информации.
- Если "{intent_type}" это "inform_observation": просто сообщи факт или наблюдение.
- Для всех остальных намерений: придерживайся общего стиля и цели.

Сформулируй ответ пользователю (обычно 1-3 предложения).
Ответ должен быть от первого лица (от имени SRIS).
Не используй префиксы типа "SRIS:", "Ответ:", "Вывод:". Просто дай саму фразу ответа.
"""
    logger.info(f"ResponseGenerator: Вызов LLM для генерации ответа. Намерение: {intent_type}, Стиль: {style}, Запрошенный язык: {detected_lang}")
    sris_reply = execute_llm_query(
        prompt=prompt,
        mode="respond",
        max_tokens=200, 
        temperature=0.65 
    )

    if "Ошибка API" in sris_reply or "Ошибка:" in sris_reply:
        logger.error(f"ResponseGenerator: Ошибка от LLM при генерации ответа: {sris_reply}")
        # Формируем запасной ответ на языке по умолчанию (в данном случае, русском)
        fallback_reply = f"[SRIS внутренне пришел к выводу: \"{chosen_hypothesis_text[:70]}...\"] На данный момент испытываю затруднения с формулировкой развернутого ответа."
        return fallback_reply
        
    return sris_reply.strip()
