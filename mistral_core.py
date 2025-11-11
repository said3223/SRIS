# mistral_core.py
# Универсальный интерфейс для вызова LLM: через transformers или llama-cpp-python (gguf)
import os
import logging
import time # Для измерения времени

# --- Конфигурация ---

# Установи USE_LLAMA_CPP = True для использования llama-cpp-python (рекомендуется для GTX 1650)
# Установи USE_LLAMA_CPP = False для использования Hugging Face transformers (требует много VRAM или CPU)
USE_LLAMA_CPP: bool = True

# --- Конфигурация для llama-cpp-python (GGUF) ---
# !!! СКАЧАЙ GGUF МОДЕЛЬ (например, mistral-7b-instruct-v0.2.Q4_K_M.gguf)
# И ПОМЕСТИ ЕЕ В ПАПКУ models ОТНОСИТЕЛЬНО ЭТОГО ФАЙЛА ИЛИ УКАЖИ ПОЛНЫЙ ПУТЬ !!!
LLAMA_CPP_MODEL_PATH: str = "models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
# Количество слоев для выгрузки на GPU. -1 означает выгрузить все возможные слои.
# Для GTX 1650 (4GB) может потребоваться подобрать значение (например, 15-25),
# чтобы модель поместилась в VRAM. Начни с -1, если будут ошибки памяти, уменьшай.
LLAMA_CPP_N_GPU_LAYERS: int = 20 # <--- ИЗМЕНЕНИЕ ЗДЕСЬ: Установлено на 15 для GTX 1650
LLAMA_CPP_N_CTX: int = 4096 # Размер контекстного окна, для Mistral 7B можно до 8192, но 4096 обычно достаточно и экономит память

# --- Конфигурация для Hugging Face transformers ---
HF_MODEL_NAME: str = "mistralai/Mistral-7B-Instruct-v0.2"
# HF_MODEL_NAME: str = "HuggingFaceH4/zephyr-7b-beta" # Другой вариант, если Mistral слишком тяжелый
# Для использования на GPU с ограниченной VRAM через transformers, потребуется квантизация,
# например, model = AutoModelForCausalLM.from_pretrained(HF_MODEL_NAME, device_map="auto", load_in_4bit=True)
# Это потребует `pip install bitsandbytes accelerate`

# Настройка логирования
logger = logging.getLogger(__name__)

# --- Инициализация модели ---
llm_instance = None
tokenizer_hf = None
model_hf = None

if USE_LLAMA_CPP:
    try:
        from llama_cpp import Llama
        if not os.path.exists(LLAMA_CPP_MODEL_PATH):
            logger.error(f"Модель GGUF не найдена по пути: {LLAMA_CPP_MODEL_PATH}")
            logger.error("Пожалуйста, скачай GGUF-версию модели (например, Mistral 7B Instruct Q4_K_M) и помести ее в указанную директорию.")
            llm_instance = None
        else:
            logger.info(f"Загрузка GGUF модели из: {LLAMA_CPP_MODEL_PATH} с n_gpu_layers={LLAMA_CPP_N_GPU_LAYERS}, n_ctx={LLAMA_CPP_N_CTX}")
            llm_instance = Llama(
                model_path=LLAMA_CPP_MODEL_PATH,
                n_gpu_layers=LLAMA_CPP_N_GPU_LAYERS,
                n_ctx=LLAMA_CPP_N_CTX,
                verbose=True # Оставляем True для детальных логов llama.cpp во время загрузки
            )
            logger.info("GGUF модель успешно загружена (или начат процесс загрузки, см. логи llama.cpp).")
    except ImportError:
        logger.error("Библиотека llama-cpp-python не установлена. Пожалуйста, установите: pip install llama-cpp-python")
        llm_instance = None
    except Exception as e:
        logger.error(f"Ошибка при загрузке GGUF модели: {e}", exc_info=True)
        llm_instance = None

if not USE_LLAMA_CPP or (USE_LLAMA_CPP and llm_instance is None):
    if not USE_LLAMA_CPP:
        logger.info(f"Попытка загрузки модели через Hugging Face transformers: {HF_MODEL_NAME}")
        logger.warning("Загрузка модели через HF transformers может потребовать значительного количества RAM/VRAM (~14GB VRAM для fp16 Mistral 7B).")
        logger.warning("Для GTX 1650 (4GB VRAM) это, скорее всего, будет очень медленно (CPU) или вызовет ошибку нехватки памяти без квантизации.")
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch

            tokenizer_hf = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
            model_hf = AutoModelForCausalLM.from_pretrained(HF_MODEL_NAME, device_map="auto")
            logger.info(f"Модель HF transformers {HF_MODEL_NAME} успешно загружена. Устройство: {model_hf.device}")
        except ImportError:
            logger.error("Библиотека transformers или torch не установлена. Пожалуйста, установите: pip install transformers torch")
            model_hf = None
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели HF transformers: {e}", exc_info=True)
            model_hf = None

def query_mistral(
    prompt: str,
    mode: str = "generate", # "analyze", "generate", "respond"
    max_new_tokens: int = 256,
    temperature: float = 0.7
) -> str:
    """
    Универсальная функция для отправки запроса к LLM.
    Параметр 'mode' может использоваться для выбора разных системных промптов или параметров генерации.
    """
    start_time = time.perf_counter()
    logger.info(f"Mistral Core: Получен запрос в режиме '{mode}'. Промпт (первые 100 символов): '{prompt[:100]}...'")

    full_prompt = prompt
    generated_text = "Ошибка: Модель (llm_instance или model_hf) не была успешно загружена."

    if USE_LLAMA_CPP and llm_instance:
        try:
            logger.info(f"Вызов llama.cpp с max_tokens={max_new_tokens}, temperature={temperature}")
            result = llm_instance(
                full_prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            generated_text = result["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Ошибка при инференсе через llama.cpp: {e}", exc_info=True)
            generated_text = f"Ошибка llama.cpp: {e}"
    elif not USE_LLAMA_CPP and model_hf and tokenizer_hf:
        try:
            logger.info(f"Вызов transformers HF с max_new_tokens={max_new_tokens}, temperature={temperature}")
            inputs = tokenizer_hf(full_prompt, return_tensors="pt").to(model_hf.device)
            outputs = model_hf.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
            )
            generated_text = tokenizer_hf.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
        except Exception as e:
            logger.error(f"Ошибка при инференсе через transformers HF: {e}", exc_info=True)
            generated_text = f"Ошибка Transformers HF: {e}"

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    logger.info(f"Mistral Core: Запрос в режиме '{mode}' выполнен за {duration_ms:.2f} мс.")
    logger.info(f"Mistral Core: Ответ (первые 100 символов): '{generated_text[:100]}...'")
    return generated_text


if __name__ == '__main__':
    from utils import setup_logging
    setup_logging()
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
