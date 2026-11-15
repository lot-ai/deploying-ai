"""
Service 2: Semantic Query
Uses a local ChromaDB PersistentClient over a small curated knowledge base
of original finance / market-microstructure notes (see data/knowledge_docs.json).
Embeddings are produced with OpenAI text-embedding-3-small.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from utils.logger import get_logger

_logs = get_logger(__name__)

# Paths relative to the assignment_chat package
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "knowledge_docs.json"
CHROMA_PATH = BASE_DIR / "chroma_db"
COLLECTION_NAME = "lot_research_knowledge"


def _get_embedding_function():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("API_GATEWAY_KEY")
    # When using the course gateway the embedding calls still need a real key
    # or the gateway must support embeddings. Fall back gracefully.
    return OpenAIEmbeddingFunction(
        api_key=api_key or "unused",
        model_name="text-embedding-3-small",
    )


def get_or_create_collection():
    """Return a persistent Chroma collection, creating & loading docs if empty."""
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    ef = _get_embedding_function()

    try:
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
        if collection.count() > 0:
            _logs.info(f"Loaded existing collection with {collection.count()} documents")
            return collection
    except Exception:
        pass

    # Create fresh
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0 and DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            docs = json.load(f)
        ids = [d["id"] for d in docs]
        texts = [f"{d['title']}. {d['text']}" for d in docs]
        metadatas = [{"title": d["title"]} for d in docs]
        collection.add(ids=ids, documents=texts, metadatas=metadatas)
        _logs.info(f"Indexed {len(docs)} knowledge documents into Chroma")
    return collection


def semantic_search(query: str, n_results: int = 3) -> str:
    """
    Perform semantic search over the Lot Research knowledge base and return
    a rephrased, analyst-style synthesis of the most relevant passages.
    Never dumps raw documents verbatim.
    """
    _logs.info(f"Semantic query: {query[:80]}...")
    try:
        collection = get_or_create_collection()
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, 5),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        _logs.error(f"Chroma query failed: {e}")
        return (
            "Semantic search is temporarily unavailable. "
            "The local knowledge base could not be queried. "
            f"Technical detail: {type(e).__name__}."
        )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    if not docs:
        return (
            "No sufficiently relevant material found in the Lot Research knowledge base "
            "for that query. Try rephrasing or ask for a broader concept."
        )

    # Build a natural synthesis rather than dumping chunks
    pieces = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        title = meta.get("title", "Note") if meta else "Note"
        # Simple distance-to-relevance heuristic (cosine distance)
        relevance = "high" if dist < 0.45 else "moderate" if dist < 0.7 else "lower"
        # Truncate long passages
        excerpt = doc if len(doc) < 320 else doc[:300].rsplit(" ", 1)[0] + "…"
        pieces.append(f"[{title} — relevance {relevance}] {excerpt}")

    synthesis = (
        "From the internal knowledge base: "
        + " | ".join(pieces)
        + " These notes are for research context only and do not constitute advice."
    )
    return synthesis
