# Supplier RAG Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local supplier retrieval app that ingests vendor table rows as LangChain documents, stores embeddings in ChromaDB, and serves Groq-grounded top-5 search results through FastAPI and a simple React UI.

**Architecture:** The backend reads vendor files from a local data folder, turns each row into one LangChain `Document`, stores embeddings in a persistent local Chroma collection, retrieves candidates for a procurement query, and asks a Groq-backed LangChain model to rank grounded results. The frontend is a small React app that submits a query and renders the returned vendors.

**Tech Stack:** Python 3.11, FastAPI, LangChain, langchain-chroma, langchain-huggingface, langchain-groq, ChromaDB, pandas, React, Vite

---

## File Map

- Create: `src/supplier_entity_mapping/api/app.py`
- Create: `src/supplier_entity_mapping/api/routes.py`
- Create: `src/supplier_entity_mapping/api/dependencies.py`
- Create: `src/supplier_entity_mapping/ingestion/tabular_loader.py`
- Create: `src/supplier_entity_mapping/ingestion/document_builder.py`
- Create: `src/supplier_entity_mapping/config.py`
- Create: `src/supplier_entity_mapping/services/index_service.py`
- Modify: `src/supplier_entity_mapping/rag/query_service.py`
- Modify: `src/supplier_entity_mapping/main.py`
- Modify: `src/supplier_entity_mapping/cli/run_pipeline.py`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/styles.css`
- Modify: `README.md`
- Create: `data/vendors/.gitkeep`

## Chunk 1: Backend Foundations

### Task 1: Add configuration and vendor data conventions

**Files:**
- Create: `src/supplier_entity_mapping/config.py`
- Modify: `src/supplier_entity_mapping/main.py`
- Create: `data/vendors/.gitkeep`

- [ ] Define application settings for data directory, Chroma persistence directory, collection name, top-k retrieval size, and Groq model name.
- [ ] Add a simple entrypoint that can expose the FastAPI app cleanly.
- [ ] Create the local vendor data folder in the repository layout.

### Task 2: Implement tabular loading and row-to-document conversion

**Files:**
- Create: `src/supplier_entity_mapping/ingestion/tabular_loader.py`
- Create: `src/supplier_entity_mapping/ingestion/document_builder.py`

- [ ] Read CSV and Excel files from the local vendor data directory with pandas.
- [ ] Normalize row values for document creation without adding cleaning or deduplication logic.
- [ ] Convert each row into exactly one LangChain `Document`.
- [ ] Store original row fields in document metadata and build searchable `page_content` from non-empty values.

### Task 3: Implement local Chroma indexing service

**Files:**
- Create: `src/supplier_entity_mapping/services/index_service.py`

- [ ] Initialize Hugging Face embeddings with `sentence-transformers/all-mpnet-base-v2`.
- [ ] Create or rebuild a Chroma collection persisted on disk.
- [ ] Load vendor rows, convert them to documents, and write them to Chroma.
- [ ] Return useful indexing summary data such as file name, rows indexed, and persistence path.

## Chunk 2: Retrieval API

### Task 4: Implement Groq-grounded query service

**Files:**
- Modify: `src/supplier_entity_mapping/rag/query_service.py`

- [ ] Retrieve candidate vendor documents from Chroma for a procurement query.
- [ ] Build a grounded prompt that instructs the Groq-backed LangChain model to prefer exact matches from retrieved context and otherwise choose the most suitable vendors from that list.
- [ ] Parse the model output into a stable top-5 response shape for the API.
- [ ] Fall back gracefully to raw retrieved candidates if LLM output is malformed or unavailable.

### Task 5: Implement FastAPI endpoints

**Files:**
- Create: `src/supplier_entity_mapping/api/app.py`
- Create: `src/supplier_entity_mapping/api/routes.py`
- Create: `src/supplier_entity_mapping/api/dependencies.py`

- [ ] Add `POST /index` to ingest a specified local vendor file.
- [ ] Add `GET /search` to return grounded top-5 vendor results for a query.
- [ ] Wire settings and services through dependency helpers instead of building them directly in route handlers.
- [ ] Enable simple CORS support for the local React frontend.

## Chunk 3: Local UI

### Task 6: Scaffold a minimal React app

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/styles.css`

- [ ] Create a small Vite-based React frontend.
- [ ] Add one input for procurement queries and a button to search.
- [ ] Call the FastAPI search endpoint and render the returned vendor list.
- [ ] Show loading, error, and empty states.

## Chunk 4: Local Workflow and Documentation

### Task 7: Wire CLI/docs for local development

**Files:**
- Modify: `src/supplier_entity_mapping/cli/run_pipeline.py`
- Modify: `README.md`

- [ ] Add a lightweight CLI entrypoint for indexing a local vendor file.
- [ ] Document required environment variables such as `GROQ_API_KEY`.
- [ ] Document how to place supplier CSV files in `data/vendors/`, run the API, and run the React frontend locally.
- [ ] Document the expected search behavior and known v1 limitations.

### Task 8: Verify the local build path

**Files:**
- Review only

- [ ] Install Python dependencies from `pyproject.toml` if needed.
- [ ] Run a backend import or syntax check.
- [ ] Run project verification commands that are available in this workspace.
- [ ] Record any remaining gaps caused by missing sample CSV data or unavailable local dependencies.
