# wikidata_client.py
import requests
import json
import logging
from typing import List, Dict, Optional, Any # Добавил Any

# Настройка логгера
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API_ENDPOINT = "https://www.wikidata.org/w/api.php" # Эндпоинт для wbsearchentities

HEADERS = {
    "User-Agent": "SRIS-Wikidata-Integrator/1.0 (https://github.com/morpheus-ai/SRIS)"
}

# ===== ФУНКЦИЯ ДЛЯ ВЫПОЛНЕНИЯ SPARQL-ЗАПРОСОВ (остается без изменений) =====
def query_wikidata(sparql_query: str) -> list:
    """
    Отправляет SPARQL-запрос к Wikidata и возвращает результат в виде списка словарей.
    """
    logger.debug(f"WikidataClient: Отправка SPARQL-запроса (первые 300 символов):\n{sparql_query[:300]}...")
    try:
        response = requests.get(
            WIKIDATA_SPARQL_ENDPOINT,
            headers=HEADERS,
            params={"query": sparql_query, "format": "json"},
            timeout=30
        )
        response.raise_for_status() 
        
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])
        
        parsed_results = []
        for item_bindings in bindings:
            parsed_item = {}
            for key, binding_details in item_bindings.items():
                parsed_item[key] = binding_details.get("value")
            parsed_results.append(parsed_item)
        
        logger.info(f"WikidataClient: Получено {len(parsed_results)} результатов для SPARQL-запроса.")
        return parsed_results

    except requests.exceptions.RequestException as e:
        logger.error(f"WikidataClient: Ошибка сетевого запроса к Wikidata (SPARQL): {e}", exc_info=True)
        return [] 
    except json.JSONDecodeError as e:
        logger.error(f"WikidataClient: Ошибка декодирования JSON ответа от Wikidata (SPARQL): {e}", exc_info=True)
        response_text_snippet = response.text[:500] if 'response' in locals() and response else 'No response object'
        logger.error(f"WikidataClient: Ответ сервера (SPARQL) (начало): {response_text_snippet}")
        return []
    except Exception as e:
        logger.error(f"WikidataClient: Неожиданная ошибка при выполнении SPARQL-запроса: {e}", exc_info=True)
        return []

# ===== НОВАЯ ФУНКЦИЯ ДЛЯ ПОИСКА СУЩНОСТЕЙ ПО МЕТКЕ =====
def search_wikidata_entities_by_label(search_term: str, lang: str = "ru", limit: int = 7) -> List[Dict[str, str]]:
    """
    Ищет сущности в Wikidata по текстовой метке, используя API wbsearchentities.
    Возвращает список словарей с QID, меткой и описанием найденных сущностей.
    """
    params = {
        "action": "wbsearchentities",
        "search": search_term,
        "language": lang,      # Язык, на котором выполняется поиск термина
        "uselang": lang,       # Язык, на котором возвращаются метки и описания
        "format": "json",
        "limit": limit,
        "props": "description" # Хотим получить и описание
    }
    logger.info(f"WikidataClient: Поиск сущностей по термину '{search_term}' (язык: {lang}, лимит: {limit}).")
    
    try:
        response = requests.get(WIKIDATA_API_ENDPOINT, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        search_results = []
        if "search" in data:
            for item in data["search"]:
                search_results.append({
                    "qid": item.get("id"),
                    "label": item.get("label"),
                    "description": item.get("description", "") # Описание может отсутствовать
                })
        logger.info(f"WikidataClient: Найдено {len(search_results)} сущностей для термина '{search_term}'.")
        return search_results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WikidataClient: Ошибка сетевого запроса к Wikidata (API Search): {e}", exc_info=True)
        return []
    except json.JSONDecodeError as e:
        logger.error(f"WikidataClient: Ошибка декодирования JSON ответа от Wikidata (API Search): {e}", exc_info=True)
        response_text_snippet = response.text[:500] if 'response' in locals() and response else 'No response object'
        logger.error(f"WikidataClient: Ответ сервера (API Search) (начало): {response_text_snippet}")
        return []
    except Exception as e:
        logger.error(f"WikidataClient: Неожиданная ошибка при поиске сущностей: {e}", exc_info=True)
        return []

# ===== ФУНКЦИЯ ДЛЯ ФОРМАТИРОВАНИЯ РЕЗУЛЬТАТОВ (остается без изменений) =====
def format_wikidata_entity_data(qid: str, sparql_results: List[Dict[str, str]]) -> Dict[str, str]:
    # ... (код этой функции остается таким же, как я приводил ранее) ...
    aggregated_data_by_lang: Dict[str, Dict[str, Any]] = {}
    for row in sparql_results:
        lang = row.get("lang")
        if not lang: continue
        if lang not in aggregated_data_by_lang:
            aggregated_data_by_lang[lang] = {
                "itemLabel": None, "itemDescription": None, "itemAltLabel": set(),
                "instanceOf": set(), "subclassOf": set()
            }
        current_lang_data = aggregated_data_by_lang[lang]
        if not current_lang_data["itemLabel"] and row.get("itemLabel"):
            current_lang_data["itemLabel"] = row.get("itemLabel")
        if not current_lang_data["itemDescription"] and row.get("itemDescription"):
            current_lang_data["itemDescription"] = row.get("itemDescription")
        if row.get("itemAltLabel"): current_lang_data["itemAltLabel"].add(row.get("itemAltLabel"))
        if row.get("instanceOfLabel") and row.get("instanceOf"):
            current_lang_data["instanceOf"].add((row.get("instanceOfLabel"), row.get("instanceOf")))
        if row.get("subclassOfLabel") and row.get("subclassOf"):
            current_lang_data["subclassOf"].add((row.get("subclassOfLabel"), row.get("subclassOf")))
    output_texts: Dict[str, str] = {}
    for lang_code, data in aggregated_data_by_lang.items():
        text_parts = []
        label = data.get("itemLabel", "Метка не найдена" if lang_code == "ru" else "Label not found")
        description = data.get("itemDescription", "Описание отсутствует" if lang_code == "ru" else "Description not available")
        text_parts.append(f"Концепция ({lang_code.upper()}): {label} (QID: {qid})")
        text_parts.append(f"Описание: {description}")
        if data.get("itemAltLabel"):
            text_parts.append(f"Также известен как: {', '.join(sorted(list(data['itemAltLabel'])))}")
        if data.get("instanceOf"):
            text_parts.append(f"Является экземпляром (типом): {', '.join([f'{io_label} (QID: {io_qid})' for io_label, io_qid in sorted(list(data['instanceOf']))])}")
        if data.get("subclassOf"):
            text_parts.append(f"Является подклассом: {', '.join([f'{so_label} (QID: {so_qid})' for so_label, so_qid in sorted(list(data['subclassOf']))])}")
        output_texts[lang_code] = "\n".join(text_parts)
        logger.info(f"Сформирован текст для QID {qid} на языке '{lang_code}'.")
    return output_texts


