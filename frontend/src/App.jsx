import { useState } from "react";

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;

function normalizeResults(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  if (Array.isArray(payload?.results)) {
    return payload.results;
  }

  if (Array.isArray(payload?.vendors)) {
    return payload.vendors;
  }

  if (Array.isArray(payload?.items)) {
    return payload.items;
  }

  return [];
}

function formatScore(score) {
  if (typeof score !== "number" || Number.isNaN(score)) {
    return null;
  }

  return score.toFixed(3);
}

function pickText(value) {
  if (value == null) {
    return "";
  }

  return String(value).trim();
}

function ResultCard({ item, index }) {
  const metadata = item?.metadata ?? {};
  const vendorName =
    pickText(item?.vendor_name) ||
    pickText(metadata?.vendor_name) ||
    pickText(metadata?.name) ||
    pickText(item?.name) ||
    `Vendor ${index + 1}`;
  const summary =
    pickText(item?.summary) ||
    pickText(item?.searchable_text) ||
    pickText(metadata?.description) ||
    pickText(metadata?.summary) ||
    pickText(item?.content) ||
    "";
  const reason = pickText(item?.reason);

  const score = formatScore(item?.score ?? item?.similarity ?? item?.distance);
  const chips = [
    pickText(metadata?.category),
    pickText(metadata?.city),
    pickText(metadata?.country),
    pickText(metadata?.address),
    pickText(metadata?.location),
  ].filter(Boolean);

  return (
    <article className="result-card">
      <div className="result-card__top">
        <div>
          <p className="result-card__rank">Result {index + 1}</p>
          <h2>{vendorName}</h2>
        </div>
        {score !== null ? (
          <span className="result-card__score">Score {score}</span>
        ) : null}
      </div>

      {summary ? <p className="result-card__summary">{summary}</p> : null}
      {reason ? <p className="result-card__summary">{reason}</p> : null}

      {chips.length ? (
        <div className="chip-row">
          {chips.map((chip, chipIndex) => (
            <span className="chip" key={`${chip}-${chipIndex}`}>
              {chip}
            </span>
          ))}
        </div>
      ) : null}

      <div className="result-card__meta">
        {metadata?.supplier_id ? <span>ID {metadata.supplier_id}</span> : null}
        {item?.rank ? <span>Rank {item.rank}</span> : null}
      </div>
    </article>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [results, setResults] = useState([]);

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      setError("Enter a supplier or procurement query.");
      setResults([]);
      setSubmittedQuery("");
      return;
    }

    setLoading(true);
    setError("");
    setSubmittedQuery(trimmedQuery);

    try {
      const response = await fetch(
        `${API_BASE_URL}/search?q=${encodeURIComponent(trimmedQuery)}`,
      );

      if (!response.ok) {
        let detail = "";
        try {
          const errorPayload = await response.json();
          detail =
            typeof errorPayload?.detail === "string" ? errorPayload.detail : "";
        } catch {
          detail = "";
        }
        throw new Error(detail || `Search failed with status ${response.status}`);
      }

      const payload = await response.json();
      setResults(normalizeResults(payload).slice(0, 5));
    } catch (fetchError) {
      setResults([]);
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "Unable to reach the search service.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Supplier RAG</p>
        <h1>Search vendor rows with grounded retrieval.</h1>
        <p className="lede">
          Query the local FastAPI backend, pull the top matches from ChromaDB,
          and review the best five vendors in a simple ranked list.
        </p>

        <form className="search-panel" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="query">
            Search suppliers
          </label>
          <input
            id="query"
            name="query"
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="e.g. industrial chemicals in Texas"
            autoComplete="off"
          />
          <button type="submit" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="status-row">
          <span>API base: {API_BASE_URL}</span>
          <span>Top 5 vendors</span>
        </div>
      </section>

      <section className="results-panel" aria-live="polite">
        {error ? <div className="alert">{error}</div> : null}

        {!error && !loading && !submittedQuery ? (
          <div className="empty-state">
            <h2>Start with a vendor query.</h2>
            <p>
              The backend will return the five best matches from your local
              supplier data.
            </p>
          </div>
        ) : null}

        {!error && loading ? (
          <div className="loading-state">Fetching vendor matches...</div>
        ) : null}

        {!error && !loading && submittedQuery && !results.length ? (
          <div className="empty-state">
            <h2>No vendors returned.</h2>
            <p>
              Try a broader query or make sure the backend has been indexed with
              your supplier file.
            </p>
          </div>
        ) : null}

        <div className="results-grid">
          {results.map((item, index) => (
            <ResultCard
              key={`${item?.id ?? item?.vendor_name ?? item?.name ?? index}`}
              item={item}
              index={index}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
