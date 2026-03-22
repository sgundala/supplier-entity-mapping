FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_LOCAL_FILES_ONLY=false
ENV VENDOR_DATA_DIR=data/raw
ENV CHROMA_PERSIST_DIR=storage/chroma
ENV CHROMA_COLLECTION_NAME=supplier_documents
ENV FRONTEND_DIST_DIR=frontend/dist

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY configs ./configs

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "supplier_entity_mapping.main:app", "--host", "0.0.0.0", "--port", "8000"]
