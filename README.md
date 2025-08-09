# SRIS
Semantic Reasoning Intelligence System

## Setup

1. Ensure you are using **Python 3.10+**.
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```
4. Configure the language model in `mistral_core.py`.
   - Set `USE_LLAMA_CPP = True` to load a local GGUF model with `llama-cpp-python` and adjust `LLAMA_CPP_MODEL_PATH`.
   - Or set `USE_LLAMA_CPP = False` to use a Hugging Face model via `transformers` and update `HF_MODEL_NAME`.

5. Start the API server:

   ```bash
   uvicorn sris_server:app --reload
   ```

The server exposes a FastAPI endpoint at `/process_query/` and interactive docs at `/docs`.
