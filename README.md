# SRIS
Semantic Reasoning Intelligence System

## FastAPI Example

Run the server with:
```bash
uvicorn sris_server:app --reload
```

Send a query:
```bash
curl -X POST "http://localhost:8000/process_query/" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "demo", "query_text": "Hello"}'
```
A typical JSON reply will contain the generated text, reasoning id, current tick and processing time.
