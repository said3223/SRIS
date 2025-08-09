# sris_server.py
import logging
import time
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

# --- Импорт основных компонентов SRIS ---
# Убедись, что все эти файлы находятся в той же директории или доступны
try:
    from sris_kernel import (
        run_sris_cycle, 
        generate_sris_response,
        get_or_build_semantic_index,
        sris_timesense # Импортируем готовый экземпляр TimeSense
    )
    sris_components_loaded = True
except ImportError as e:
    logging.basicConfig(level=logging.ERROR)
    logging.error(f"Критическая ошибка: не удалось импортировать компоненты SRIS. {e}")
    sris_components_loaded = False

# --- Настройка логирования ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Модели данных для API ---
class QueryRequest(BaseModel):
    user_id: str = Field("default_user", description="Уникальный идентификатор пользователя")
    query_text: str = Field(..., description="Текстовый запрос пользователя", min_length=1)

class QueryResponse(BaseModel):
    sris_response_text: str
    reasoning_id: Optional[str]
    current_sris_tick: int
    processing_time_ms: float

# --- Создание экземпляра FastAPI ---
app = FastAPI(
    title="SRIS - Semantic Reasoning Intelligence System API",
    description="API для взаимодействия с ядром смыслоцентричного интеллекта SRIS.",
    version="1.0-Prometheus"
)

# --- Событие "startup": загрузка моделей при старте сервера ---
@app.on_event("startup")
async def startup_event():
    logger.info("Сервер SRIS запускается... Инициализация моделей и компонентов...")
    if not sris_components_loaded:
        logger.critical("Компоненты SRIS не были загружены. Сервер не сможет работать корректно.")
        return

    try:
        # Принудительная инициализация семантического индекса
        get_or_build_semantic_index(rebuild=False) 
        logger.info("Семантический индекс памяти проверен и готов к работе.")
        logger.info("Все компоненты SRIS успешно инициализированы. Сервер готов к приему запросов.")
    except Exception as e:
        logger.critical(f"Критическая ошибка при инициализации компонентов на старте сервера: {e}", exc_info=True)


# --- API Эндпоинт для обработки запросов ---
@app.post("/process_query/", response_model=QueryResponse)
async def process_user_query(request: QueryRequest):
    if not sris_components_loaded:
        raise HTTPException(status_code=503, detail="SRIS Core components are not available.")

    start_time = time.time()
    logger.info(f"Получен запрос от user_id: '{request.user_id}', query_text: '{request.query_text[:100]}...'")

    input_dict = {"text": request.query_text, "audio": None, "vision": None}

    try:
        # Запускаем ресурсоемкие функции в отдельном потоке, чтобы не блокировать сервер
        sris_reasoning_result = await run_in_threadpool(run_sris_cycle, input_dict)

        if sris_reasoning_result and sris_reasoning_result.get("status") == "ok":
            sris_final_text = await run_in_threadpool(generate_sris_response, sris_reasoning_result["full_reasoning_chain"])
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000

            response_data = QueryResponse(
                sris_response_text=sris_final_text,
                reasoning_id=sris_reasoning_result.get("reasoning_id"),
                current_sris_tick=sris_timesense.get_current_tick(),
                processing_time_ms=round(processing_time, 2)
            )
            return response_data
        else:
            error_details = (sris_reasoning_result or {}).get("full_reasoning_chain", {}).get("error_message", "Неизвестная ошибка в цикле SRIS")
            logger.error(f"Ошибка в цикле SRIS: {error_details}")
            raise HTTPException(status_code=500, detail=f"Internal SRIS Error: {error_details}")

    except Exception as e:
        logger.error(f"Неожиданная ошибка при обработке запроса в /process_query/: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected server error.")

# --- Корневой эндпоинт для проверки статуса ---
@app.get("/")
def read_root():
    return {"SRIS_Status": "Alive", "Core_Version": "1.0-Prometheus", "Docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("sris_server:app", host="0.0.0.0", port=8000)
