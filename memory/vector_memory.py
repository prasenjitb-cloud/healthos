import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

embedder = SentenceTransformer("all-MiniLM-L6-v2")

DIM = 384
INDEX_FILE = "medical_memory.index"
TEXT_FILE = "medical_memory.txt"

index = faiss.IndexFlatL2(DIM)
memory_store = []

if os.path.exists(INDEX_FILE) and os.path.exists(TEXT_FILE):
    index = faiss.read_index(INDEX_FILE)
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        memory_store = f.read().splitlines()

def save_memory():
    faiss.write_index(index, INDEX_FILE)
    with open(TEXT_FILE, "w", encoding="utf-8") as f:
        for item in memory_store:
            f.write(item + "\n")

def add_to_memory(text):
    embedding = embedder.encode([text])
    index.add(np.array(embedding).astype("float32"))
    memory_store.append(text)
    save_memory()

def search_memory(query, k=3):
    if index.ntotal == 0:
        return []

    query_embedding = embedder.encode([query])
    distances, indices = index.search(
        np.array(query_embedding).astype("float32"), k
    )

    return [memory_store[i] for i in indices[0] if i < len(memory_store)]
