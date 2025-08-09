from interactive_knowledge_importer import run_interactive_importer

if __name__ == "__main__":
    # Перед запуском этого скрипта, убедись, что LlamaIndex Settings 
    # (LLM и EmbedModel) корректно инициализируются при импорте 
    # semantic_memory_index.py (что обычно происходит, если они там в глобальной области видимости).
    # Также убедись, что папка для индекса существует или может быть создана.
    run_interactive_importer()

