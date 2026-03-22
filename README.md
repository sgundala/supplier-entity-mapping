# Supplier RAG App

Local supplier retrieval app built with FastAPI, LangChain, Hugging Face embeddings, ChromaDB, Groq, and a simple React UI.

## What It Does

- reads supplier data from `data/raw/`
- converts each CSV or Excel row into one LangChain `Document`
- stores embeddings in local ChromaDB
- retrieves supplier candidates for a procurement query
- asks a Groq-backed LangChain model to rank grounded top matches
- shows the top 5 suppliers in a React UI

## Project Layout

- `data/raw/`: place your supplier CSV or Excel files here
- `storage/chroma/`: local Chroma persistence directory
- `src/supplier_entity_mapping/`: backend and indexing logic
- `frontend/`: local React UI

## Environment

Create a `.env` file or export these variables:

```bash
GROQ_API_KEY=your_key_here
GROQ_MODEL_NAME=llama-3.1-8b-instant
HF_LOCAL_FILES_ONLY=false
VENDOR_DATA_DIR=data/raw
CHROMA_PERSIST_DIR=storage/chroma
CHROMA_COLLECTION_NAME=supplier_documents
RETRIEVAL_TOP_K=10
RESULT_LIMIT=5
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Backend Setup

Install the Python dependencies from `pyproject.toml`, then run:

```bash
python -m supplier_entity_mapping.cli.run_pipeline --file-name your-suppliers.csv
uvicorn supplier_entity_mapping.main:app --reload
```

API endpoints:

- `POST /index`
- `GET /search?q=industrial chemicals in texas`
- `GET /health`

`POST /index` accepts JSON like:

```json
{
  "file_name": "your-suppliers.csv"
}
```

## Frontend Setup

From `frontend/`:

```bash
npm install
npm run dev
```

The UI expects the FastAPI backend at `http://localhost:8000` by default.

## Docker

The repository includes a single-image Docker setup that serves both the FastAPI backend and the built React frontend.

Build:

```bash
docker build -t supplier-rag:latest .
```

Run:

```bash
docker run --rm -p 8000:8000 \
  -e GROQ_API_KEY=your_key_here \
  -e HF_LOCAL_FILES_ONLY=false \
  supplier-rag:latest
```

Then open:

- `http://localhost:8000`

Notes:

- `.env` is excluded from git and from the Docker build context
- pass secrets like `GROQ_API_KEY` at runtime, not in the image
- use `HF_LOCAL_FILES_ONLY=false` in containers so the embedding model can download on first run
- the container uses `data/raw/` as the default input directory

### Docker Compose

For one-command startup:

```bash
docker compose up --build
```

Then open:

- `http://localhost:8000`

The compose setup:

- reads runtime secrets from your local `.env`
- mounts `data/raw/` into the container
- persists Chroma data in `storage/chroma/`
- forces `HF_LOCAL_FILES_ONLY=false` so first-run model downloads work inside the container

## Search Behavior

- retrieval is grounded in your local ChromaDB supplier index
- Groq ranks only from the retrieved candidate suppliers
- each supplier row is treated as exactly one LangChain document
- no cleaning, deduplication, or canonical entity mapping is done in v1

## Notes

- supported input file types: `.csv`, `.xlsx`, `.xls`
- set `HF_LOCAL_FILES_ONLY=true` if the embedding model is already cached and you want offline startup behavior
- if Groq output cannot be parsed, the API falls back to raw retrieved candidates
- initial indexing requires at least one non-empty supplier file in `data/raw/`
