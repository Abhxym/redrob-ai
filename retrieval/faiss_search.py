"""
retrieval/faiss_search.py

Builds a FAISS dense retrieval index over candidate profiles using
BAAI/bge-small-en-v1.5 sentence embeddings.

Outputs:
  data/candidate_embeddings.npy  — shape (N, 384)
  data/faiss_index.bin           — IndexFlatIP (cosine via normalized L2)
"""

import json
import pathlib
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

PROFILES_PATH = pathlib.Path("data/candidate_profiles.json")
EMBEDDINGS_PATH = pathlib.Path("data/candidate_embeddings.npy")
INDEX_PATH = pathlib.Path("data/faiss_index.bin")
MODEL_NAME = "BAAI/bge-small-en-v1.5"


def load_profiles(path: pathlib.Path) -> tuple[list[str], list[str]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ids = [d["candidate_id"] for d in data]
    texts = [d["profile_text"] for d in data]
    return ids, texts


def build_index(embeddings: np.ndarray) -> faiss.Index:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine after L2 norm
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    return index


def search(
    query: str,
    model: SentenceTransformer,
    index: faiss.Index,
    candidate_ids: list[str],
    top_k: int = 5,
) -> list[dict]:
    query_emb = model.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = index.search(query_emb, top_k)
    return [
        {"candidate_id": candidate_ids[i], "score": float(scores[0][rank])}
        for rank, i in enumerate(indices[0])
    ]


def main():
    print("Loading profiles...")
    candidate_ids, texts = load_profiles(PROFILES_PATH)

    print(f"Encoding {len(texts)} profiles with {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype="float32")

    print(f"Embeddings shape: {embeddings.shape}")
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"Saved embeddings -> {EMBEDDINGS_PATH}")

    print("Building FAISS index...")
    index = build_index(embeddings.copy())  # copy because normalize_L2 is in-place
    faiss.write_index(index, str(INDEX_PATH))
    print(f"Saved FAISS index -> {INDEX_PATH}  ({index.ntotal} vectors)")

    # --- Test retrieval ---
    query = """
    Need machine learning engineer with Python and recommendation systems experience.
    """
    print(f"\nTest query: {query.strip()}")
    print("-" * 50)

    results = search(query, model, index, candidate_ids, top_k=5)
    for rank, r in enumerate(results, 1):
        print(f"  #{rank}  {r['candidate_id']}  score={r['score']:.4f}")


if __name__ == "__main__":
    main()
