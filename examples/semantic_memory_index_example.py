from semantic_memory_index import (
    get_or_build_semantic_index,
    query_semantic_memory,
    INDEX_STORAGE_DIR,
)
import os

if __name__ == "__main__":
    logger.info("--- Тестирование модуля semantic_memory_index.py с интеграцией Wikidata и Core Knowledge ---")
    
    FORCE_REBUILD_NOW = True 
    
    current_rebuild_flag = FORCE_REBUILD_NOW 
    if not current_rebuild_flag and not os.path.exists(os.path.join(INDEX_STORAGE_DIR, "docstore.json")):
        logger.info("Хранилище индекса не найдено, будет выполнена принудительная перестройка индекса.")
        current_rebuild_flag = True

    logger.info(f"Попытка получить/построить индекс с rebuild={current_rebuild_flag}")
    index_instance = get_or_build_semantic_index(rebuild=current_rebuild_flag)

    if index_instance:
        logger.info("Семантический индекс успешно инициализирован и готов к использованию.")
        test_queries = [
            "Кто твой создатель?",
            "Что такое OASIS в контексте SRIS?" # Тест для истории
        ]
        for query in test_queries:
            logger.info(f"\n--- Выполнение тестового запроса: '{query}' ---")
            # --- ИЗМЕНЕНО: Передаем index_instance в функцию ---
            search_results = query_semantic_memory(index=index_instance, query_text=query, similarity_top_k=1)
            if search_results:
                for i, result in enumerate(search_results):
                    logger.info(
                        f"  Результат #{i+1} (Источник: {result.get('source')}, "
                        f"Topic: {result.get('topic')}, "
                        f"Score: {result.get('score')} ):"
                    )
                    logger.info(f"    Text Preview: {result.get('text_preview')}")
            elif search_results == []:
                 logger.info("  Для данного запроса релевантных записей в памяти не найдено.")
            else: 
                 logger.warning("  Не удалось получить результаты.")
    else:
        logger.error("Не удалось создать или загрузить семантический индекс. Тестирование прервано.")
    logger.info("--- Тестирование модуля semantic_memory_index.py завершено ---")

