import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DIM = 384
INDEX_FILE = os.path.join(BASE_DIR, "medical_memory.index")
TEXT_FILE = os.path.join(BASE_DIR, "medical_memory.txt")

_index = None
_memory_store = None
_embedder = None


def init_memory():
    """
    Initialize FAISS index, embedding model, and load persisted memory.
    """
    global _index, _memory_store, _embedder

    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    _index = faiss.IndexFlatL2(DIM)
    _memory_store = []

    if os.path.exists(INDEX_FILE) and os.path.exists(TEXT_FILE):
        _index = faiss.read_index(INDEX_FILE)
        with open(TEXT_FILE, "r", encoding="utf-8") as f:
            _memory_store = f.read().splitlines()


def _save_memory():
    """
    Persist FAISS index and memory store to disk.
    """
    faiss.write_index(_index, INDEX_FILE)
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for item in _memory_store:
            f.write(item + "\n")


def add_to_memory(text: str):
    if _index is None or _embedder is None:
        raise RuntimeError("Memory not initialized. Call init_memory() first.")

    embedding = _embedder.encode([text])
    _index.add(np.array(embedding).astype("float32"))
    _memory_store.append(text)
    _save_memory()


def search_memory(query: str, k: int = 3):
    if _index is None or _index.ntotal == 0:
        return []

    query_embedding = _embedder.encode([query])
    _, indices = _index.search(
        np.array(query_embedding).astype("float32"), k
    )

    return [
        _memory_store[i]
        for i in indices[0]
        if i < len(_memory_store)
    ]
