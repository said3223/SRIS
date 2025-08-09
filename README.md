# SRIS

Semantic Reasoning Intelligence System

## Системные требования
- Python 3.10+
- Git
- CUDA Toolkit и cuDNN (для работы через GPU)

## Подготовка окружения
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Модели
Для `llama-cpp-python` требуется заранее скачать GGUF-модель (например, `mistral-7b-instruct-v0.2.Q4_K_M.gguf`) и поместить её в папку `models` в корне проекта. Путь к файлу настраивается в `mistral_core.py`.

## Запуск API
```bash
uvicorn sris_server:app --reload
```
