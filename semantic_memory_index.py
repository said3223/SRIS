# semantic_memory_index.py
import os
import json
import logging
from typing import List, Dict, Any, Optional, Set
import uuid

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

# --- Импорт из соседних модулей SRIS ---
logger_smfs_imported = False
try:
    from semantic_memory_fs import SMFS_BASE_DIR, load_chain_from_fs
    logger_smfs_imported = True
except ImportError:
    SMFS_BASE_DIR = "semantic_memory_storage"
    def load_chain_from_fs(uid: str, sub_directory: Optional[str] = None) -> Optional[Dict[str, Any]]:
        logging.error(f"ЗАГЛУШКА: Функция load_chain_from_fs не была корректно импортирована...")
        return None

wikidata_client_available = False
try:
    from wikidata_client import query_wikidata, format_wikidata_entity_data
    wikidata_client_available = True
    logging.info("wikidata_client.py успешно импортирован в semantic_memory_index.py.")
except ImportError:
    logging.error("НЕ УДАЛОСЬ ИМПОРТИРОВАТЬ wikidata_client.py. Загрузка концепций из Wikidata будет невозможна.")
    def query_wikidata(sparql_query: str) -> list: 
        logging.error("ЗАГЛУШКА: вызвана query_wikidata, но wikidata_client не импортирован.")
        return []
    def format_wikidata_entity_data(qid: str, sparql_results: List[Dict[str, str]]) -> Dict[str, str]: 
        logging.error("ЗАГЛУШКА: вызвана format_wikidata_entity_data, но wikidata_client не импортирован.")
        return {}

# --- Конфигурация ---
INDEX_STORAGE_DIR = os.path.join(SMFS_BASE_DIR, "_llama_index_storage") 
EMBED_MODEL_NAME = 'all-MiniLM-L6-v2'
OLLAMA_LLM_MODEL_NAME = "mistral" 
OLLAMA_LLM_BASE_URL = "http://localhost:11434"

QID_LIST_AI_CONCEPTS = [
    "Q11660", "Q2539", "Q121169", "Q30642", "Q179089",
]

CORE_SRIS_KNOWLEDGE = [
    {
        "id": "sris_creator_info_ru", "lang": "ru",
        "text": "Мой создатель – Саид Кулмаков. Он разработал меня, SRIS (Semantic Reasoning Intelligence System), как смыслоцентричный интеллект. Саид Кулмаков родился 14 марта 1982 года. Он проживает в городе Астана, Республика Казахстан, и работает супервайзером на производстве завода Кока-Кола.",
        "metadata": {"source": "core_sris_knowledge", "topic": "creator_information", "creator_name": "Саид Кулмаков"}
    },
    {
        "id": "sris_creator_info_en", "lang": "en",
        "text": "My creator is Said Kulmakov. He developed me, SRIS (Semantic Reasoning Intelligence System), as a meaning-centric intelligence. Said Kulmakov was born on March 14, 1982. He lives in Astana city, Republic of Kazakhstan, and works as a supervisor at the Coca-Cola plant production.",
        "metadata": {"source": "core_sris_knowledge", "topic": "creator_information", "creator_name": "Said Kulmakov"}
    }
]

logger = logging.getLogger(__name__)

try:
    Settings.llm = Ollama(model=OLLAMA_LLM_MODEL_NAME, base_url=OLLAMA_LLM_BASE_URL)
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL_NAME, device="cuda") 
    logger.info(f"LlamaIndex Settings сконфигурированы: LLM='{OLLAMA_LLM_MODEL_NAME}', EmbedModel='{EMBED_MODEL_NAME}' (device: cuda)")
except Exception as e:
    logger.error(f"Ошибка при конфигурации LlamaIndex Settings: {e}", exc_info=True)

def _convert_chain_to_document_text(chain_data: Dict[str, Any]) -> str:
    text_parts = [
        f"Input Summary: {chain_data.get('perception_struct', {}).get('summary', 'N/A')}",
        f"Goal: {chain_data.get('goal', {}).get('concept', 'N/A')} (Priority: {chain_data.get('goal', {}).get('priority', 'N/A')})",
        f"Chosen Hypothesis: {chain_data.get('chosen_hypothesis', {}).get('hypothesis', 'N/A')} (Score: {chain_data.get('chosen_hypothesis', {}).get('score', 'N/A')})",
        f"Action Plan: {chain_data.get('action_plan', {}).get('action_plan', 'N/A')}",
        f"Affective State: {chain_data.get('affect', {}).get('emotional_label', 'N/A')} (Valence: {chain_data.get('affect', {}).get('valence', 0)}, Arousal: {chain_data.get('affect', {}).get('arousal', 0)})",
        f"Determined Emotion: {chain_data.get('emotion', {}).get('dominant_emotion', 'N/A')}",
        f"Communication Intent: {chain_data.get('communication_intent', {}).get('intent_type', 'N/A')} (Style: {chain_data.get('communication_intent', {}).get('style', 'N/A')})"
    ]
    effects = chain_data.get('effects', [])
    if effects:
        effects_summary = ", ".join([e.get('concept', 'unknown_effect') for e in effects[:3]])
        text_parts.append(f"Key Predicted Effects: {effects_summary}")
    return "\n".join(filter(None, text_parts))

def _load_all_reasoning_chains_as_documents() -> List[Document]:
    documents: List[Document] = []
    if not os.path.exists(SMFS_BASE_DIR) or not logger_smfs_imported:
        logger.warning(f"Директория '{SMFS_BASE_DIR}' не найдена или semantic_memory_fs не импортирован. Пропуск загрузки цепочек рассуждений SRIS.")
        return documents
    logger.info(f"Загрузка цепочек рассуждений SRIS из: {SMFS_BASE_DIR}")
    for entry_name in os.listdir(SMFS_BASE_DIR):
        full_path = os.path.join(SMFS_BASE_DIR, entry_name)
        if os.path.isfile(full_path) and entry_name.startswith("reasoning_chain_") and entry_name.endswith(".json"):
            chain_id = entry_name.replace("reasoning_chain_", "").replace(".json", "")
            chain_data = load_chain_from_fs(chain_id) 
            if chain_data:
                doc_text = _convert_chain_to_document_text(chain_data)
                metadata = {
                    "source": "sris_reasoning_chain", "chain_id": chain_id,
                    "timestamp": chain_data.get("timestamp", "N/A"),
                    "goal_concept": chain_data.get("goal", {}).get("concept", "N/A"),
                    "filename": entry_name,
                    "input_text_preview": chain_data.get("input_text","")[:100]
                }
                documents.append(Document(text=doc_text, metadata=metadata))
    logger.info(f"Загружено и подготовлено {len(documents)} документов из цепочек рассуждений SRIS.")
    return documents

def _load_wikidata_concepts_as_documents(qids_to_load: List[str]) -> List[Document]:
    documents: List[Document] = []
    if not wikidata_client_available:
        logger.warning("Wikidata client не доступен. Пропуск загрузки концепций из Wikidata.")
        return documents
    logger.info(f"Загрузка концепций ИИ из Wikidata для QIDs: {qids_to_load}")
    
    # ИСПРАВЛЕННЫЙ SPARQL-ШАБЛОН С ОДИНАРНЫМИ СКОБКАМИ
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
    
    for qid in qids_to_load:
        logger.info(f"Обработка QID: {qid} из Wikidata...")
        actual_query = sparql_template.replace("{QID_PLACEHOLDER}", qid)
        sparql_results = query_wikidata(actual_query)
        if sparql_results:
            formatted_texts_by_lang = format_wikidata_entity_data(qid, sparql_results)
            for lang_code, text_content in formatted_texts_by_lang.items():
                if text_content:
                    concept_label_in_doc = "Unknown Concept"
                    try:
                        first_line = text_content.split('\n')[0]
                        if '(QID:' in first_line:
                            concept_label_in_doc = first_line.split('(QID:')[0].replace(f"Концепция ({lang_code.upper()}): ","").strip()
                    except Exception: pass
                    metadata = {
                        "source": "wikidata_ai_concept", "wikidata_qid": qid,
                        "language": lang_code, "concept_label": concept_label_in_doc
                    }
                    documents.append(Document(text=text_content, metadata=metadata))
        else:
            logger.warning(f"Для QID {qid} не получено результатов из Wikidata или произошла ошибка.")
    logger.info(f"Загружено и подготовлено {len(documents)} документов из концепций Wikidata.")
    return documents

def _load_core_sris_knowledge_as_documents() -> List[Document]:
    documents: List[Document] = []
    logger.info(f"Загрузка ключевых знаний о SRIS (количество записей: {len(CORE_SRIS_KNOWLEDGE)})...")
    for knowledge_item in CORE_SRIS_KNOWLEDGE:
        doc_text = knowledge_item.get("text")
        if not doc_text:
            logger.warning(f"Пропущена запись в CORE_SRIS_KNOWLEDGE без текста: {knowledge_item.get('id')}")
            continue
        metadata = knowledge_item.get("metadata", {}).copy()
        metadata["language"] = knowledge_item.get("lang", "unknown")
        metadata["doc_id"] = knowledge_item.get("id", f"core_knowledge_{uuid.uuid4()}")
        documents.append(Document(text=doc_text, metadata=metadata))
    logger.info(f"Загружено и подготовлено {len(documents)} документов из ключевых знаний о SRIS.")
    return documents

def get_or_build_semantic_index(rebuild: bool = False) -> Optional[VectorStoreIndex]:
    if not os.path.exists(INDEX_STORAGE_DIR):
        logger.info(f"Директория для индекса '{INDEX_STORAGE_DIR}' не найдена, будет создана.")
        os.makedirs(INDEX_STORAGE_DIR, exist_ok=True)
    index_file_path = os.path.join(INDEX_STORAGE_DIR, "docstore.json")
    index_possibly_exists = os.path.exists(index_file_path)

    if not rebuild and index_possibly_exists:
        logger.info(f"Загрузка существующего индекса из '{INDEX_STORAGE_DIR}'...")
        try:
            storage_context = StorageContext.from_defaults(persist_dir=INDEX_STORAGE_DIR)
            index = load_index_from_storage(storage_context) 
            logger.info("Существующий индекс успешно загружен.")
            return index
        except Exception as e:
            logger.error(f"Ошибка при загрузке существующего индекса: {e}. Попытка перестроить.", exc_info=True)
            return get_or_build_semantic_index(rebuild=True) 
    else:
        if rebuild: logger.info(f"Принудительная перестройка индекса (rebuild=True)...")
        else: logger.info(f"Индекс в '{INDEX_STORAGE_DIR}' не найден. Построение нового индекса...")
        
        sris_chain_documents = _load_all_reasoning_chains_as_documents()
        wikidata_concept_documents = _load_wikidata_concepts_as_documents(QID_LIST_AI_CONCEPTS)
        core_knowledge_documents = _load_core_sris_knowledge_as_documents()
        
        all_documents = sris_chain_documents + wikidata_concept_documents + core_knowledge_documents
        
        if not all_documents:
            logger.warning("Нет документов для построения индекса. Индекс не будет создан.")
            return None
            
        logger.info(f"Всего будет проиндексировано документов: {len(all_documents)}")
        try:
            index = VectorStoreIndex.from_documents(all_documents) 
            index.storage_context.persist(persist_dir=INDEX_STORAGE_DIR)
            logger.info(f"Новый индекс построен и сохранен в '{INDEX_STORAGE_DIR}'.")
            return index
        except Exception as e:
            logger.error(f"Критическая ошибка при построении или сохранении нового индекса: {e}", exc_info=True)
            return None

def add_documents_to_sris_index(new_documents: List[Document]) -> bool:
    if not new_documents:
        logger.info("add_documents_to_sris_index: Нет новых документов для добавления.")
        return True
    logger.info(f"add_documents_to_sris_index: Попытка добавить {len(new_documents)} новых документов в индекс.")
    try:
        index = get_or_build_semantic_index(rebuild=False) 
        if index is None:
            logger.warning("add_documents_to_sris_index: Базовый индекс не найден/не создан. Попытка создать индекс только из новых документов.")
            if not os.path.exists(INDEX_STORAGE_DIR): os.makedirs(INDEX_STORAGE_DIR, exist_ok=True)
            index = VectorStoreIndex.from_documents(new_documents)
        else:
            logger.info(f"add_documents_to_sris_index: Вставка {len(new_documents)} новых документов в существующий/базовый индекс...")
            for doc_to_insert in new_documents:
                index.insert(doc_to_insert)
        
        logger.info("add_documents_to_sris_index: Сохранение обновленного индекса на диск...")
        index.storage_context.persist(persist_dir=INDEX_STORAGE_DIR)
        logger.info(f"add_documents_to_sris_index: {len(new_documents)} новых документов успешно добавлены, индекс сохранен.")
        return True
    except Exception as e:
        logger.error(f"add_documents_to_sris_index: Ошибка при добавлении документов в индекс: {e}", exc_info=True)
        return False

def query_semantic_memory(index: VectorStoreIndex, query_text: str, similarity_top_k: int = 3) -> Optional[List[Dict[str, Any]]]:
    # ... ИЗМЕНЕНО: принимаем индекс как аргумент ...
    logger.info(f"Выполнение семантического запроса к предоставленному индексу: '{query_text}' (top_k={similarity_top_k})")
    if index is None:
        logger.error("В query_semantic_memory передан пустой индекс (None). Запрос не может быть выполнен.")
        return None
    try:
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        retrieved_nodes_with_scores = retriever.retrieve(query_text) 
        results = []
        if retrieved_nodes_with_scores:
            logger.info(f"Найдено {len(retrieved_nodes_with_scores)} релевантных узлов в памяти.")
            for node_with_score in retrieved_nodes_with_scores:
                results.append({
                    "source": node_with_score.metadata.get("source", "unknown"),
                    "chain_id": node_with_score.metadata.get("chain_id"), 
                    "wikidata_qid": node_with_score.metadata.get("wikidata_qid"),
                    "language": node_with_score.metadata.get("language"),
                    "concept_label": node_with_score.metadata.get("concept_label"),
                    "topic": node_with_score.metadata.get("topic"), 
                    "filename": node_with_score.metadata.get("filename"),
                    "score": round(node_with_score.score, 4),
                    "text_preview": node_with_score.get_text()[:300] + "...", 
                    "full_text": node_with_score.get_text(), 
                    "metadata": node_with_score.metadata
                })
        else:
            logger.info("Релевантных записей в памяти не найдено для данного запроса.")
        return results
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса к семантическому индексу: {e}", exc_info=True)
        return None

# --- Пример использования и тестирования модуля ---
if __name__ == "__main__":
    from utils import setup_logging
    setup_logging()
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
