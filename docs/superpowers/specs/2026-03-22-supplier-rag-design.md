# Supplier RAG Design

Date: 2026-03-22

## Goal

Build a simple local supplier retrieval product that:

- reads a vendor Excel or tabular file from a local data folder
- converts each table row into one LangChain `Document`
- creates embeddings with Hugging Face `all-mpnet-base-v2`
- stores vectors in local ChromaDB
- exposes retrieval through a FastAPI backend
- uses a LangChain LLM with Groq to rank and format grounded results from retrieved context
- provides a simple React UI to search and display the top 5 vendor results

This first version is retrieval-only. It does not perform data cleaning, normalization, deduplication, or canonical supplier mapping.

## Scope

Included in v1:

- local file-based vendor data ingestion
- one row to one document preprocessing
- semantic retrieval with ChromaDB
- Groq-backed LangChain answer layer over retrieved vendors
- FastAPI search API
- React search interface
- top 5 ranked vendor results

Excluded from v1:

- supplier entity resolution
- abbreviation expansion
- canonical entity generation
- BM25 or hybrid retrieval
- FAISS
- LLM answer synthesis
- authentication or user management

## Architecture

The system has four simple parts:

1. Data folder
   A local folder such as `data/vendors/` stores input Excel or tabular files.

2. Backend
   A FastAPI application loads vendor data, converts rows to LangChain documents, builds embeddings, stores them in ChromaDB, and serves search results.

3. Vector store
   ChromaDB runs locally as an embedded dependency and persists the vector database on disk.

4. LLM layer
   A LangChain LLM backed by Groq receives the procurement query and retrieved vendor context, then selects and formats the best grounded vendor matches.

5. Frontend
   A simple React UI sends a procurement query to the backend and displays the top 5 vendors.

## Data Flow

### Indexing flow

1. User places a vendor file in the local data folder.
2. Backend reads the file into rows.
3. Each row is converted into exactly one LangChain `Document`.
4. `page_content` is built by joining row values into searchable text.
5. `metadata` stores the original row fields for display.
6. Embeddings are created with `all-mpnet-base-v2`.
7. Documents and embeddings are stored in local ChromaDB.

### Search flow

1. User enters a procurement query in the React UI.
2. React sends the query to a FastAPI endpoint.
3. FastAPI performs semantic similarity search in ChromaDB.
4. FastAPI passes the query and retrieved vendor context to a LangChain LLM using Groq.
5. The LLM selects the best grounded vendor matches from the retrieved context.
6. Backend returns the top 5 matching vendor results.
7. React displays the ranked vendor list.

## Document Preprocessing

Preprocessing in v1 is intentionally minimal.

Each row from the source table becomes one LangChain `Document`.

- `page_content`: a plain text representation of the row, created by joining the meaningful field values
- `metadata`: structured original fields such as vendor name, address, city, country, category, and description

There is no chunk splitting. One row is one chunk and one document.

## LLM Prompt Behavior

The Groq-backed LangChain prompt should be simple and grounded.

The model must:

- use only the retrieved vendor context
- first look for an exact or very close match to the procurement query
- if no exact match exists, choose the most suitable vendors from the retrieved list
- return the top 5 vendors in ranked order
- avoid inventing suppliers that are not present in the retrieved context

This keeps ChromaDB responsible for retrieval while Groq handles selection and response formatting.

## API Design

The FastAPI backend should expose a minimal API surface.

### `POST /index`

Purpose:
Build or rebuild the Chroma index from the local vendor file.

Response:
- status
- number of rows indexed
- Chroma persistence location

### `GET /search?q=...`

Purpose:
Run semantic search for a procurement query and return grounded LLM-ranked vendor results.

Response:
- query
- total returned
- top 5 vendor results

Each result should include:
- rank
- vendor name
- searchable text or summary
- metadata fields needed by the UI
- similarity score if available

## Frontend Design

The React UI should remain small and focused.

Main screen:

- query input box
- search button
- loading state
- empty state
- results list

Each result card or row should show:

- vendor name
- category if present
- address or location if present
- short description if present

No chat interface is needed in v1.

## Suggested Project Structure

```text
data/
  vendors/

docs/
  superpowers/
    specs/

frontend/

src/supplier_entity_mapping/
  api/
  ingestion/
  embeddings/
  retrieval/
  rag/
```

This structure should stay lightweight. The important boundary is that API code should call services instead of embedding retrieval logic directly in route handlers.

## Testing

The first test set should cover:

1. Row-to-document conversion
   Verify each source row becomes one LangChain `Document` with the expected `page_content` and `metadata`.

2. Index creation
   Verify documents are embedded and persisted into ChromaDB successfully.

3. Search endpoint
   Verify a query returns results in the expected top-5 API response shape.

4. Frontend display
   Verify the React UI can render the returned vendor list for a search response.

## Future Extensions

The v1 design should leave room to add later:

- supplier deduplication and canonical entities
- BM25 or hybrid retrieval
- metadata filters
- reranking
- downstream supplier risk or sourcing workflows

These extensions should come after the basic local retrieval product is working end to end.
