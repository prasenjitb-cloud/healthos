"""
vector_memory.py

Semantic memory store for HealthOS patient history and medical encounters.

Supports:
1. FAISS + sentence-transformers when available.
2. High-performance offline pure-numpy embedding/cosine similarity store
   when FAISS is not installed.
"""

import os
import json
import numpy as np
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DIM = 384
INDEX_FILE = os.path.join(BASE_DIR, "medical_memory.index")
TEXT_FILE = os.path.join(BASE_DIR, "medical_memory.txt")
JSON_STORE_FILE = os.path.join(BASE_DIR, "medical_memory.json")

_index = None
_memory_store: List[str] = []
_metadata_store: List[Dict[str, Any]] = []
_embedder = None
_use_faiss = False
_initialized = False


def _simple_vectorize(text: str, dim: int = DIM) -> np.ndarray:
    """
    Zero-dependency deterministic hashing vectorizer.
    Produces a normalized float32 embedding vector of fixed dimension.
    """
    vec = np.zeros(dim, dtype=np.float32)
    tokens = text.lower().replace(".", " ").replace(",", " ").split()
    if not tokens:
        return vec

    for i, token in enumerate(tokens):
        h = hash(token)
        idx1 = abs(h) % dim
        idx2 = abs(hash(token[::-1])) % dim
        vec[idx1] += 1.0
        vec[idx2] += 0.5
        vec[(idx1 + i) % dim] += 0.25

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def init_memory():
    """
    Initialize memory index, embedding model, and load persisted memory from disk.
    Gracefully falls back to pure numpy storage if FAISS is not installed.
    """
    global _index, _memory_store, _metadata_store, _embedder, _use_faiss, _initialized

    _memory_store = []
    _metadata_store = []

    # Attempt to load sentence_transformers & faiss
    try:
        import sentence_transformers
        import faiss
        _embedder = sentence_transformers.SentenceTransformer("all-MiniLM-L6-v2")
        _index = faiss.IndexFlatL2(DIM)
        _use_faiss = True
    except Exception:
        _embedder = None
        _index = None
        _use_faiss = False

    # Load persisted memories
    if os.path.exists(JSON_STORE_FILE):
        try:
            with open(JSON_STORE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                _memory_store = [item.get("text", "") for item in saved]
                _metadata_store = saved
        except Exception:
            _memory_store = []
            _metadata_store = []
    elif os.path.exists(TEXT_FILE):
        try:
            with open(TEXT_FILE, "r", encoding="utf-8") as f:
                _memory_store = f.read().splitlines()
                _metadata_store = [{"text": t} for t in _memory_store]
        except Exception:
            _memory_store = []
            _metadata_store = []

    # If using FAISS, index existing records
    if _use_faiss and _memory_store and _index is not None and _embedder is not None:
        try:
            embeddings = _embedder.encode(_memory_store)
            _index.add(np.array(embeddings).astype("float32"))
        except Exception:
            pass

    _initialized = True


def _save_memory():
    """Persists memories to disk."""
    global _memory_store, _metadata_store

    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for item in _memory_store:
            f.write(item + "\n")

    with open(JSON_STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(_metadata_store, f, indent=2)

    if _use_faiss and _index is not None:
        try:
            import faiss
            faiss.write_index(_index, INDEX_FILE)
        except Exception:
            pass


def add_to_memory(text: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Adds a new encounter or patient record to memory and persists it.
    """
    global _index, _memory_store, _metadata_store, _embedder, _use_faiss, _initialized

    if not _initialized:
        init_memory()

    entry = {
        "text": text,
        "metadata": metadata or {},
    }

    if _use_faiss and _index is not None and _embedder is not None:
        try:
            embedding = _embedder.encode([text])
            _index.add(np.array(embedding).astype("float32"))
        except Exception:
            pass

    _memory_store.append(text)
    _metadata_store.append(entry)
    _save_memory()


def search_memory(query: str, k: int = 3) -> List[str]:
    """
    Searches the memory store for top-k semantically relevant records.
    """
    global _index, _memory_store, _embedder, _use_faiss, _initialized

    if not _initialized:
        init_memory()

    if not _memory_store:
        return []

    # FAISS search if available
    if _use_faiss and _index is not None and _embedder is not None and _index.ntotal > 0:
        try:
            query_embedding = _embedder.encode([query])
            _, indices = _index.search(np.array(query_embedding).astype("float32"), min(k, len(_memory_store)))
            return [_memory_store[i] for i in indices[0] if i < len(_memory_store)]
        except Exception:
            pass

    # High-performance cosine similarity fallback via numpy
    query_vec = _simple_vectorize(query, DIM)
    scores = []
    for idx, item in enumerate(_memory_store):
        item_vec = _simple_vectorize(item, DIM)
        sim = float(np.dot(query_vec, item_vec))
        scores.append((sim, idx))

    scores.sort(key=lambda x: x[0], reverse=True)
    top_indices = [idx for sim, idx in scores[:k] if sim > 0.05 or len(scores) <= k]
    if not top_indices and scores:
        top_indices = [scores[0][1]]

    return [_memory_store[i] for i in top_indices]


def search_patient_history(patient_name: str, k: int = 3) -> List[str]:
    """Searches memory specifically for records mentioning the given patient."""
    if not patient_name:
        return []
    return search_memory(f"Patient {patient_name} appointment symptoms history", k=k)
