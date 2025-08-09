from mistral_core import query_mistral, USE_LLAMA_CPP, llm_instance, model_hf, tokenizer_hf

if __name__ == '__main__':
    logger.info("--- Тестирование mistral_core.py ---")
    model_ready = False
    if USE_LLAMA_CPP:
        if llm_instance:
            model_ready = True
    else:
        if model_hf and tokenizer_hf:
            model_ready = True

    if not model_ready:
        logger.error("Ни одна из моделей не была успешно загружена или сконфигурирована. Тестирование невозможно.")
    else:
        test_prompt_analyze = "Проанализируй следующий текст и предоставь структурированный анализ. Входной текст: 'Погода сегодня отличная! Солнечно и тепло.'"
        test_prompt_generate = "Контекст: Надвигается шторм. Цель: Обеспечить безопасность. Сгенерируй 3 гипотезы."
        test_prompt_respond = "Привет! Как твои дела?"

        logger.info("\n--- Тест режима 'analyze' ---")
        response_analyze = query_mistral(test_prompt_analyze, mode="analyze", max_new_tokens=150)
        print(f"Ответ 'analyze':\n{response_analyze}\n")

        logger.info("\n--- Тест режима 'generate' ---")
        response_generate = query_mistral(test_prompt_generate, mode="generate", max_new_tokens=200)
        print(f"Ответ 'generate':\n{response_generate}\n")

        logger.info("\n--- Тест режима 'respond' ---")
        response_respond = query_mistral(test_prompt_respond, mode="respond", max_new_tokens=50)
        print(f"Ответ 'respond':\n{response_respond}\n")

