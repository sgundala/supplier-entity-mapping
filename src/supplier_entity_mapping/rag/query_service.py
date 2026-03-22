from __future__ import annotations

import re
from textwrap import dedent

import orjson
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from supplier_entity_mapping.config import AppSettings
from supplier_entity_mapping.models.schemas import (
    LlmSearchResponse,
    SearchResponse,
    SearchResult,
)


class QueryService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._embeddings: HuggingFaceEmbeddings | None = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.settings.embedding_model_name,
                model_kwargs={"local_files_only": self.settings.hf_local_files_only},
            )
        return self._embeddings

    def _vector_store(self) -> Chroma:
        return Chroma(
            collection_name=self.settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_persist_dir),
        )

    @staticmethod
    def _normalize_text(value: object) -> str:
        return str(value).strip().lower()

    def _metadata_match_results(self, query: str) -> list[SearchResult]:
        normalized_query = self._normalize_text(query)
        query_tokens = {token for token in re.split(r"\W+", normalized_query) if token}
        if not query_tokens:
            return []

        vector_store = self._vector_store()
        payload = vector_store.get(include=["documents", "metadatas"])

        scored_results: list[tuple[int, SearchResult]] = []
        documents = payload.get("documents", [])
        metadatas = payload.get("metadatas", [])

        for document, metadata in zip(documents, metadatas, strict=False):
            if not metadata:
                continue

            best_score = 0
            for field in ("client_category", "supplier_name", "supplier_hq", "sourcing_country"):
                raw_value = metadata.get(field)
                if not raw_value:
                    continue
                normalized_value = self._normalize_text(raw_value)
                value_tokens = {token for token in re.split(r"\W+", normalized_value) if token}

                if normalized_query == normalized_value:
                    best_score = max(best_score, 100)
                elif normalized_query in normalized_value:
                    best_score = max(best_score, 80)
                elif query_tokens and query_tokens.issubset(value_tokens):
                    best_score = max(best_score, 60)

            if best_score == 0:
                continue

            vendor_name = (
                metadata.get("supplier_name")
                or metadata.get("vendor_name")
                or metadata.get("name")
                or "Vendor"
            )
            scored_results.append(
                (
                    best_score,
                    SearchResult(
                        rank=0,
                        vendor_name=str(vendor_name),
                        summary=document,
                        metadata=dict(metadata),
                        score=float(best_score),
                    ),
                )
            )

        scored_results.sort(
            key=lambda item: (
                -item[0],
                int(item[1].metadata.get("source_row_number", 0)),
            )
        )

        lexical_results: list[SearchResult] = []
        for index, (_, result) in enumerate(scored_results, start=1):
            lexical_results.append(
                SearchResult(
                    rank=index,
                    vendor_name=result.vendor_name,
                    summary=result.summary,
                    metadata=result.metadata,
                    score=result.score,
                )
            )

        return lexical_results

    def _candidate_results(self, query: str) -> list[SearchResult]:
        lexical_results = self._metadata_match_results(query)
        vector_store = self._vector_store()
        docs_with_scores = vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=self.settings.retrieval_top_k,
        )

        results: list[SearchResult] = []
        for rank, (document, score) in enumerate(docs_with_scores, start=1):
            metadata = dict(document.metadata)
            vendor_name = (
                metadata.get("supplier_name")
                or metadata.get("vendor_name")
                or metadata.get("name")
                or f"Vendor {rank}"
            )
            results.append(
                SearchResult(
                    rank=rank,
                    vendor_name=str(vendor_name),
                    summary=document.page_content,
                    metadata=metadata,
                    score=score,
                )
            )

        combined_results: list[SearchResult] = []
        seen_rows: set[int | None] = set()
        for candidate in lexical_results + results:
            row_number = candidate.metadata.get("source_row_number")
            if row_number in seen_rows:
                continue
            seen_rows.add(row_number)
            combined_results.append(
                SearchResult(
                    rank=len(combined_results) + 1,
                    vendor_name=candidate.vendor_name,
                    summary=candidate.summary,
                    metadata=candidate.metadata,
                    score=candidate.score,
                )
            )

            if len(combined_results) >= self.settings.retrieval_top_k:
                break

        return combined_results

    def _build_prompt(self, query: str, candidates: list[SearchResult]) -> str:
        candidate_lines = []
        for candidate in candidates:
            candidate_lines.append(
                dedent(
                    f"""
                    Candidate {candidate.rank}
                    vendor_name: {candidate.vendor_name}
                    score: {candidate.score}
                    metadata: {candidate.metadata}
                    content:
                    {candidate.summary}
                    """
                ).strip()
            )

        joined_candidates = "\n\n".join(candidate_lines)
        return dedent(
            f"""
            You are ranking supplier search results for a procurement user.

            Use only the candidate suppliers provided below.
            First look for an exact or very close match to the user's query.
            If there is no exact match, choose the most suitable suppliers from the list.
            Do not invent any suppliers that are not in the candidate list.
            Return strictly valid JSON with this shape:
            {{
              "results": [
                {{
                  "vendor_name": "string",
                  "reason": "short explanation",
                  "source_row_number": 1
                }}
              ]
            }}
            Use the exact `source_row_number` value from the candidate metadata.
            Do not renumber candidates.
            Do not include any explanation outside the JSON.

            User query:
            {query}

            Candidate suppliers:
            {joined_candidates}
            """
        ).strip()

    @staticmethod
    def _parse_json_payload(content: str) -> dict:
        normalized = content.strip()
        fenced_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", normalized, flags=re.DOTALL)
        if fenced_blocks:
            normalized = fenced_blocks[-1].strip()
        elif normalized.startswith("```"):
            normalized = normalized.strip("`")
            if normalized.startswith("json"):
                normalized = normalized[4:].strip()
        return orjson.loads(normalized)

    def _llm_rank_results(self, query: str, candidates: list[SearchResult]) -> list[SearchResult]:
        if not self.settings.groq_api_key or not candidates:
            return candidates[: self.settings.result_limit]

        llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model_name,
            temperature=0,
        )
        response = llm.invoke(self._build_prompt(query, candidates))
        content = getattr(response, "content", "")
        if isinstance(content, list):
            content = "".join(str(item) for item in content)

        payload = self._parse_json_payload(content)
        selection = LlmSearchResponse.model_validate(payload)

        selected_results: list[SearchResult] = []
        used_keys: set[tuple[str, int | None]] = set()
        for item in selection.results:
            matched = None
            for candidate in candidates:
                candidate_row = candidate.metadata.get("source_row_number")
                if item.source_row_number is not None and candidate_row == item.source_row_number:
                    matched = candidate
                    break
                if candidate.vendor_name.lower() == item.vendor_name.lower():
                    matched = candidate
                    break

            if matched is None:
                continue

            dedupe_key = (matched.vendor_name.lower(), matched.metadata.get("source_row_number"))
            if dedupe_key in used_keys:
                continue

            used_keys.add(dedupe_key)
            selected_results.append(
                SearchResult(
                    rank=len(selected_results) + 1,
                    vendor_name=matched.vendor_name,
                    summary=matched.summary,
                    reason=item.reason,
                    metadata=matched.metadata,
                    score=matched.score,
                )
            )

            if len(selected_results) >= self.settings.result_limit:
                break

        return selected_results or candidates[: self.settings.result_limit]

    def search(self, query: str) -> SearchResponse:
        candidates = self._candidate_results(query)
        try:
            ranked_results = self._llm_rank_results(query, candidates)
            grounded_by_llm = bool(self.settings.groq_api_key)
        except Exception:
            ranked_results = candidates[: self.settings.result_limit]
            grounded_by_llm = False

        return SearchResponse(
            query=query,
            total_returned=len(ranked_results),
            results=ranked_results[: self.settings.result_limit],
            grounded_by_llm=grounded_by_llm,
        )
