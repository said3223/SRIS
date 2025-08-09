from wikidata_client import (
    query_wikidata,
    format_wikidata_entity_data,
    search_wikidata_entities_by_label,
)

if __name__ == "__main__":
    print("--- Начинаем тест запроса и форматирования данных из Wikidata ---")

    # --- Тест 1: Извлечение и форматирование данных для известного QID ---
    qid_to_test = "Q11660" # Искусственный интеллект
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
    actual_query = sparql_template.replace("{QID_PLACEHOLDER}", qid_to_test)
    
    print(f"\nВыполняем SPARQL-запрос для QID: {qid_to_test}...")
    results = query_wikidata(actual_query)

    if results:
        print(f"Получено сырых результатов из Wikidata: {len(results)}")
        print(f"\n--- Форматирование данных для QID: {qid_to_test} ---")
        formatted_texts = format_wikidata_entity_data(qid_to_test, results)
        if formatted_texts:
            for lang_code, text_blob in formatted_texts.items():
                print(f"\n--- Готовый текст для индексации ({lang_code.upper()}) ---")
                print(text_blob)
        else:
            print("Не удалось сформировать текст из результатов.")
    elif isinstance(results, list) and not results: 
        print(f"Для QID {qid_to_test} не найдено результатов, соответствующих запросу, или произошла ошибка (см. логи выше).")
    
    print("\n--- Тест 1 завершен ---")

    # --- Тест 2: Поиск сущностей по названию с помощью новой функции ---
    print("\n--- Тест 2: Поиск сущностей по названию ---")
    search_term_ru = "Машинное обучение"
    print(f"\nИщем сущности для: '{search_term_ru}' (язык: ru)")
    found_entities_ru = search_wikidata_entities_by_label(search_term_ru, lang="ru", limit=3)
    if found_entities_ru:
        for entity in found_entities_ru:
            print(f"  QID: {entity.get('qid')}, Метка: {entity.get('label')}, Описание: {entity.get('description')}")
    else:
        print("  Сущности не найдены.")

    search_term_en = "Python programming language"
    print(f"\nИщем сущности для: '{search_term_en}' (язык: en)")
    found_entities_en = search_wikidata_entities_by_label(search_term_en, lang="en", limit=3)
    if found_entities_en:
        for entity in found_entities_en:
            print(f"  QID: {entity.get('qid')}, Label: {entity.get('label')}, Description: {entity.get('description')}")
    else:
        print("  Entities not found.")

    print("\n--- Тестирование Wikidata Client полностью завершено ---")

