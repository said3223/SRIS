# SRIS

Semantic Reasoning Intelligence System (SRIS) is an experimental Python framework for meaning‑centric reasoning.  The project bundles multiple modules such as perception analysis, goal formation and memory management.  SRIS can be used interactively through a Tkinter based GUI or remotely through a FastAPI service.

## Repository structure
- `sris_kernel.py` – core reasoning cycle and GUI implementation.
- `sris_server.py` – FastAPI wrapper exposing the SRIS cycle.
- `semantic_memory_index.py` – semantic memory built with LlamaIndex and Ollama.
- Additional modules (`mistral_core.py`, `motivation_engine.py`, etc.) provide individual reasoning components.

## Diagrams
The repository contains several PNG diagrams illustrating the architecture and data flow:
- `79A39398-3FCA-4845-BEBD-8A6A154BFF24.png`
- `DB80BEC9-6F46-4641-B245-8CDF718942D4.png`
- `B4B028D4-A72B-47CA-9F98-5500942E4B4C.png`
- `911754CF-7795-4EA5-86F2-E1F99C53DD78.png`
- `04428AA0-38F8-44BD-96F5-C6DE5F0D62E9.png`
- `54C7FFE3-7FA1-470E-81ED-FFF22F3DD163.png`
These images describe how SRIS modules interact, how memory is structured and how reasoning results are generated.

## Prerequisites
- Python 3.11 or later
- [Ollama](https://ollama.ai/) running on `localhost:11434` for LLM access
- LlamaIndex
- FastAPI and Uvicorn
- Tkinter (usually included with Python)
- Optionally `llama-cpp-python` or `transformers` depending on your LLM setup

Install the required Python packages for a minimal setup:
```bash
pip install fastapi uvicorn llama-index pillow
```

## Running the SRIS GUI
1. Make sure Ollama is running and the required GGUF or HuggingFace model is available.
2. Launch the GUI application:
```bash
python sris_kernel.py
```
A chat window will appear where queries can be sent to SRIS.

## Running the FastAPI server
Start the API server with Uvicorn:
```bash
uvicorn sris_server:app --reload
```
At startup the server loads SRIS components and builds the semantic index as shown in `sris_server.py` lines 30–61 and defines the `/process_query/` endpoint on lines 65–103.
Open `http://localhost:8000/docs` for interactive API documentation.

## Usage examples
### GUI
After running `python sris_kernel.py`, type a message and press Enter.  SRIS processes the request and prints responses in the chat window.

### API
Send a POST request to the `/process_query/` endpoint:
```bash
curl -X POST http://localhost:8000/process_query/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user1", "query_text": "Привет, что ты умеешь?"}'
```
The response will contain the generated text, reasoning ID and processing statistics.

## License
This project is licensed under the Apache-2.0 License.
