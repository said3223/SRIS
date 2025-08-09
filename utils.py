# utils.py
import logging
import json
import re
from typing import Dict, Any, Optional, Union

DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(level: int = logging.INFO, fmt: str = DEFAULT_LOG_FORMAT) -> None:
    """Configure root logging for the application.

    This should be called once at application startup.
    If handlers already exist, only the level will be updated.
    """
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level, format=fmt)
    else:
        root_logger.setLevel(level)
    logging.getLogger(__name__).debug("Logging configured")

try:
    from mistral_core import query_mistral
    mistral_core_available = True
    logging.info("mistral_core.py успешно импортирован в utils.py.")
except ImportError:
    logging.error("НЕ УДАЛОСЬ ИМПОРТИРОВАТЬ mistral_core.py. Вызовы LLM будут возвращать ошибку.")
    mistral_core_available = False
    def query_mistral(prompt: str, mode: str, max_tokens: int, temperature: float) -> str:
        return "Ошибка: Модуль mistral_core не доступен."

logger = logging.getLogger(__name__)

def _extract_json_from_response(text: str) -> Optional[str]:
    """
    Извлекает ПЕРВЫЙ валидный JSON-объект из строки, даже если он обрамлен текстом 
    или ```json ... ``` блоками. Устойчив к "мусору" после JSON.
    """
    # Сначала ищем JSON, обернутый в ```json ... ```
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        logger.debug("Найден JSON-блок в ```json ... ```")
        return match.group(1)

    # Если не нашли, ищем первый символ '{'
    first_brace = text.find('{')
    if first_brace == -1:
        logger.warning("Не найдено открывающей скобки '{' в ответе LLM.")
        return None

    # Начиная с первой '{', ищем соответствующую ей '}'
    open_braces = 0
    for i, char in enumerate(text[first_brace:]):
        if char == '{':
            open_braces += 1
        elif char == '}':
            open_braces -= 1
        
        if open_braces == 0:
            # Мы нашли конец первого полного JSON объекта
            json_str = text[first_brace : first_brace + i + 1]
            logger.debug(f"Первый полный JSON-объект извлечен: {json_str[:200]}...")
            return json_str
            
    logger.warning("Не найдено закрывающей скобки '}' для первого JSON-объекта.")
    return None

def execute_llm_query(
    prompt: str,
    mode: str = "default",
    max_tokens: int = 512,
    temperature: float = 0.7,
    expect_json: bool = False
) -> Union[str, Dict[str, Any]]:
    """
    Централизованная функция для выполнения запросов к LLM.
    Теперь использует улучшенный извлекатель JSON.
    """
    logger.info(f"Utils: Передача запроса в LLM ядро (mistral_core) в режиме '{mode}' (max_tokens: {max_tokens}, temp: {temperature}, expect_json: {expect_json})")

    if not mistral_core_available:
        error_msg = "Ошибка: Модель (llm_instance или model_hf) не была успешно загружена."
        if expect_json:
            return {"error": "LLM_NOT_AVAILABLE", "message": error_msg}
        return error_msg
        
    llm_response_text = query_mistral(prompt, mode, max_tokens, temperature)

    if not expect_json:
        return llm_response_text

    logger.info("Ожидается JSON-ответ. Запуск извлечения и парсинга...")
    json_str = _extract_json_from_response(llm_response_text)
    
    if json_str:
        try:
            parsed_json = json.loads(json_str)
            logger.info("JSON-ответ успешно распарсен.")
            return parsed_json
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}", exc_info=True)
            logger.error(f"Некорректная JSON-строка, полученная от LLM: {json_str}")
            return {"error": "JSON_DECODE_ERROR", "message": str(e), "raw_response": json_str}
    else:
        logger.error("JSON-объект не найден в ответе LLM.")
        return {"error": "JSON_NOT_FOUND", "message": "No JSON object found in the LLM response.", "raw_response": llm_response_text}
