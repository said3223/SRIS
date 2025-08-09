# SRIS

Semantic Reasoning Intelligence System

## Project Overview

SRIS is a collection of modules that together provide a meaning-centric reasoning system built around a local large language model.  The main entry points are:

- `sris_kernel.py` – runs the reasoning cycle and includes a simple Tkinter GUI when executed directly.
- `sris_server.py` – FastAPI server exposing an API around the kernel.
- `mistral_core.py` – wrapper around `llama-cpp-python` or HuggingFace Transformers used to query a Mistral 7B model.
- `interactive_knowledge_importer.py` – example tool for loading knowledge into the semantic memory index.

Other modules implement perception analysis, motivation, semantic memory management and many additional pieces that are orchestrated by `sris_kernel.py`.

## Installation

The project requires Python 3.9+ with CUDA available for GPU acceleration.  You also need a quantized **Mistral 7B** model in GGUF format.  Place the downloaded model file inside the `models/` directory or adjust `LLAMA_CPP_MODEL_PATH` in `mistral_core.py` to point at its location.

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

## Running SRIS

### FastAPI Server

Start the HTTP API for SRIS via Uvicorn:

```bash
uvicorn sris_server:app --reload
```

The server loads the model on startup and exposes `/process_query/` for sending reasoning requests.  API documentation is available at `/docs` when the server is running.

### GUI Kernel

To experiment with the kernel in a simple GUI, run:

```bash
python sris_kernel.py
```

A Tkinter window will open where you can send queries and observe log output in the terminal.

