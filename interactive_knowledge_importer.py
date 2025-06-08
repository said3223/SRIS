# interactive_knowledge_importer.py
import logging
from typing import List, Dict, Any

# Предполагаем, что эти модули находятся в том же каталоге или доступны
# и что в них уже настроено логирование и глобальные Settings для LlamaIndex
try:
    from wikidata_client import search_wikidata_entities_by_label, query_wikidata, format_wikidata_entity_data
    from semantic_memory_index import add_documents_to_sris_index, QID_LIST_AI_CONCEPTS, CORE_SRIS_KNOWLEDGE 
    # QID_LIST_AI_CONCEPTS и CORE_SRIS_KNOWLEDGE импортируются для примера, 
    # чтобы показать, что они уже могут быть в индексе
    from llama_index.core import Document
    modules_loaded = True
except ImportError as e:
    logging.basicConfig(level=logging.ERROR) # Установим базовый логгер, если другие не сработали
    logging.error(f"Ошибка импорта необходимых модулей: {e}")
    logging.error("Пожалуйста, убедитесь, что wikidata_client.py и semantic_memory_index.py находятся в той же директории или доступны через PYTHONPATH.")
    modules_loaded = False

# Настройка логгера для этого скрипта
logger = logging.getLogger(__name__)
if not logger.handlers and modules_loaded: # Настраиваем, только если основные модули загрузились
    # Используем существующую конфигурацию логирования, если она была установлена другими модулями,
    # или устанавливаем свою, если это первый запуск.
    # Для простоты, предполагаем, что logging.basicConfig уже был вызван в одном из импортируемых модулей.
    # Если нет, можно добавить здесь:
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    pass


def run_interactive_importer():
    if not modules_loaded:
        logger.error("Необходимые модули не загружены. Запуск интерактивного импортера невозможен.")
        return

    logger.info("--- Интерактивный импортер знаний из Wikidata для SRIS ---")
    
    # Сначала убедимся, что базовый индекс может быть загружен или создан
    # (это также инициализирует Settings LlamaIndex, если это еще не сделано)
    # add_documents_to_sris_index вызовет get_or_build_semantic_index внутри себя.
    # Мы можем сделать "пустой" вызов, чтобы просто проверить/инициализировать индекс.
    logger.info("Проверка/инициализация семантического индекса...")
    add_documents_to_sris_index([]) # Пустой список документов, просто для инициализации индекса если нужно
    logger.info("Семантический индекс готов к работе.")

    while True:
        print("\nВведите термин для поиска в Wikidata (или 'выход' для завершения):")
        search_term = input("> ").strip()

        if not search_term:
            continue
        if search_term.lower() == 'выход':
            logger.info("Завершение работы интерактивного импортера.")
            break

        lang = input("На каком языке искать (ru/en, по умолчанию ru): ").strip().lower() or "ru"
        limit_str = input("Максимальное количество результатов поиска (по умолчанию 5): ").strip()
        limit = 5
        try:
            if limit_str:
                limit = int(limit_str)
        except ValueError:
            logger.warning(f"Неверный формат лимита, используется значение по умолчанию: 5")
            limit = 5
        
        logger.info(f"Поиск сущностей для '{search_term}' на языке '{lang}'...")
        found_entities = search_wikidata_entities_by_label(search_term, lang=lang, limit=limit)

        if not found_entities:
            print(f"По термину '{search_term}' ничего не найдено. Попробуйте другой запрос.")
            continue

        print("\nНайденные сущности:")
        for i, entity in enumerate(found_entities):
            print(f"  {i+1}. {entity.get('label', 'N/A')} (QID: {entity.get('qid', 'N/A')})")
            print(f"      Описание: {entity.get('description', 'Нет описания')}")
        
        while True:
            try:
                choice_str = input(f"Введите номер сущности для импорта (1-{len(found_entities)}) или 0 для нового поиска: ").strip()
                choice = int(choice_str)
                if 0 <= choice <= len(found_entities):
                    break
                else:
                    print(f"Неверный номер. Пожалуйста, введите число от 0 до {len(found_entities)}.")
            except ValueError:
                print("Пожалуйста, введите число.")

        if choice == 0:
            continue

        selected_entity = found_entities[choice - 1]
        selected_qid = selected_entity.get("qid")
        selected_label = selected_entity.get("label", "Неизвестная сущность")

        if not selected_qid:
            logger.error(f"У выбранной сущности '{selected_label}' отсутствует QID. Пропуск.")
            continue

        logger.info(f"Выбрана сущность: {selected_label} (QID: {selected_qid}). Запрос полной информации...")

        # Тот же SPARQL-шаблон, что и в semantic_memory_index.py
        sparql_template = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT ?item ?itemLabel ?itemDescription ?itemAltLabel ?instanceOf ?instanceOfLabel ?subclassOf ?subclassOfLabel ?lang
        WHERE {
          BIND(wd:{QID_PLACEHOLDER} AS ?item)
          VALUES ?lang { "ru" "en" }
          ?item rdfs:label ?itemLabel. FILTER(LANG(?itemLabel) = ?lang)
          OPTIONAL { ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = ?lang) }
          OPTIONAL { ?item skos:altLabel ?itemAltLabel. FILTER(LANG(?itemAltLabel) = ?lang) }
          OPTIONAL { ?item wdt:P31 ?instanceOfRaw. ?instanceOfRaw rdfs:label ?instanceOfLabel. FILTER(LANG(?instanceOfLabel) = ?lang) BIND(REPLACE(STR(?instanceOfRaw), "http://www.wikidata.org/entity/", "") AS ?instanceOf) }
          OPTIONAL { ?item wdt:P279 ?subclassOfRaw. ?subclassOfRaw rdfs:label ?subclassOfLabel. FILTER(LANG(?subclassOfLabel) = ?lang) BIND(REPLACE(STR(?subclassOfRaw), "http://www.wikidata.org/entity/", "") AS ?subclassOf) }
        }
        """
        actual_query = sparql_template.replace("{QID_PLACEHOLDER}", selected_qid)
        sparql_results = query_wikidata(actual_query)

        if not sparql_results:
            logger.warning(f"Не удалось получить подробную информацию для QID {selected_qid} ('{selected_label}').")
            continue
            
        formatted_texts_by_lang = format_wikidata_entity_data(selected_qid, sparql_results)
        
        new_docs_for_index: List[Document] = []
        for lang_code, text_content in formatted_texts_by_lang.items():
            if text_content:
                metadata = {
                    "source": "wikidata_interactive_import", # Отмечаем источник
                    "wikidata_qid": selected_qid,
                    "language": lang_code,
                    "concept_label": selected_label, # Метка на языке поиска
                    "search_term_used": search_term # Сохраняем исходный поисковый запрос
                }
                new_docs_for_index.append(Document(text=text_content, metadata=metadata))
                logger.info(f"Подготовлен документ для QID: {selected_qid}, Язык: {lang_code}, Метка: {selected_label}")
        
        if new_docs_for_index:
            logger.info(f"Добавление {len(new_docs_for_index)} документов в семантический индекс...")
            success = add_documents_to_sris_index(new_docs_for_index)
            if success:
                print(f"Информация о '{selected_label}' (QID: {selected_qid}) успешно добавлена в семантическую память SRIS.")
            else:
                print(f"Ошибка при добавлении информации о '{selected_label}' в память.")
        else:
            logger.warning(f"Не удалось подготовить документы для индексации для QID {selected_qid}.")

if __name__ == "__main__":
    # Перед запуском этого скрипта, убедись, что LlamaIndex Settings 
    # (LLM и EmbedModel) корректно инициализируются при импорте 
    # semantic_memory_index.py (что обычно происходит, если они там в глобальной области видимости).
    # Также убедись, что папка для индекса существует или может быть создана.
    run_interactive_importer()
