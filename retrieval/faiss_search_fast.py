"""
retrieval/faiss_search_fast.py

Ultra-fast FAISS implementation optimized for speed.
Uses HashingVectorizer (no fit needed) + pre-computed embeddings.
"""

import json
import pathlib
import numpy as np
import faiss
from sklearn.feature_extraction.text import HashingVectorizer
import time

PROFILES_PATH = pathlib.Path("data/candidate_profiles.json")
EMBEDDINGS_PATH = pathlib.Path("data/candidate_embeddings.npy")
INDEX_PATH = pathlib.Path("data/faiss_index.bin")
VECTORIZER_DIM = 384


def load_profiles(path: pathlib.Path) -> tuple:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ids = [d["candidate_id"] for d in data]
    texts = [d["profile_text"] for d in data]
    return ids, texts


def build_embeddings_fast(texts: list) -> np.ndarray:
    """Generate embeddings using HashingVectorizer (no fitting needed)"""
    vectorizer = HashingVectorizer(
        n_features=VECTORIZER_DIM,
        norm='l2',
        alternate_sign=False,
        dtype=np.float32
    )
    embeddings = vectorizer.transform(texts).toarray().astype('float32')
    return embeddings, vectorizer


def build_index_fast(embeddings: np.ndarray) -> faiss.Index:
    """Build FAISS index with GPU acceleration if available"""
    dim = embeddings.shape[1]
    
    # Try GPU if available, fall back to CPU
    try:
        # Use GPU if available
        res = faiss.StandardGpuResources()
        cpu_index = faiss.IndexFlatIP(dim)
        index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
    except:
        # Fall back to CPU
        index = faiss.IndexFlatIP(dim)
    
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    return index


def search_fast(query: str, vectorizer, index: faiss.Index, 
                candidate_ids: list, top_k: int = 5) -> list:
    """Fast search without re-fitting vectorizer"""
    query_emb = vectorizer.transform([query]).toarray().astype('float32')
    faiss.normalize_L2(query_emb)
    scores, indices = index.search(query_emb, top_k)
    
    return [
        {"candidate_id": candidate_ids[i], "score": float(scores[0][rank])}
        for rank, i in enumerate(indices[0])
    ]


def main():
    start_time = time.time()
    
    print("=" * 60)
    print("FAISS FAST RETRIEVAL")
    print("=" * 60)
    
    # Load
    t1 = time.time()
    candidate_ids, texts = load_profiles(PROFILES_PATH)
    load_time = time.time() - t1
    print(f"[OK] Loaded {len(texts)} profiles ({load_time:.3f}s)")

    # Embed
    t1 = time.time()
    embeddings, vectorizer = build_embeddings_fast(texts)
    embed_time = time.time() - t1
    print(f"[OK] Generated embeddings {embeddings.shape} ({embed_time:.3f}s)")
    
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"[OK] Saved -> {EMBEDDINGS_PATH}")

    # Index
    t1 = time.time()
    index = build_index_fast(embeddings.copy())
    index_time = time.time() - t1
    print(f"[OK] Built FAISS index ({index_time:.3f}s)")
    
    faiss.write_index(faiss.index_gpu_to_cpu(index) if hasattr(index, 'index') else index, 
                      str(INDEX_PATH))
    print(f"[OK] Saved -> {INDEX_PATH}")

    # Search
    query = "Need machine learning engineer with Python and recommendation systems experience."
    print(f"\nQuery: {query}")
    print("-" * 60)
    
    t1 = time.time()
    results = search_fast(query, vectorizer, index, candidate_ids, top_k=5)
    search_time = time.time() - t1
    print(f"Search time: {search_time*1000:.2f}ms\n")
    
    for rank, r in enumerate(results, 1):
        print(f"  #{rank}  {r['candidate_id']}  score={r['score']:.4f}")

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"Total time: {total_time:.3f}s")
    print(f"  Load: {load_time:.3f}s")
    print(f"  Embed: {embed_time:.3f}s")
    print(f"  Index: {index_time:.3f}s")
    print(f"  Search: {search_time*1000:.2f}ms")
    print("=" * 60)


if __name__ == "__main__":
    main()
