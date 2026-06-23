"""
retrieval/faiss_search_lite.py

Lightweight FAISS implementation without torch overhead.
Uses sklearn for embeddings instead of sentence-transformers.
"""

import json
import pathlib
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer

PROFILES_PATH = pathlib.Path("data/candidate_profiles.json")
EMBEDDINGS_PATH = pathlib.Path("data/candidate_embeddings.npy")
INDEX_PATH = pathlib.Path("data/faiss_index.bin")


def load_profiles(path: pathlib.Path) -> tuple:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ids = [d["candidate_id"] for d in data]
    texts = [d["profile_text"] for d in data]
    return ids, texts


def build_embeddings(texts: list) -> np.ndarray:
    """Generate TF-IDF embeddings from text"""
    vectorizer = TfidfVectorizer(
        max_features=384,  # Match expected dimension
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True
    )
    embeddings = vectorizer.fit_transform(texts).toarray()
    # Pad to 384 dimensions if needed
    if embeddings.shape[1] < 384:
        padded = np.zeros((embeddings.shape[0], 384), dtype='float32')
        padded[:, :embeddings.shape[1]] = embeddings.astype('float32')
        embeddings = padded
    else:
        embeddings = embeddings[:, :384].astype('float32')
    
    return embeddings.astype('float32')


def build_index(embeddings: np.ndarray) -> faiss.Index:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    return index


def search(query: str, model_embeddings: np.ndarray, vectorizer, index: faiss.Index, 
           candidate_ids: list, top_k: int = 5) -> list:
    """Search index with query"""
    query_emb = vectorizer.transform([query]).toarray()
    
    # Pad to 384 dimensions
    if query_emb.shape[1] < 384:
        padded = np.zeros((1, 384), dtype='float32')
        padded[:, :query_emb.shape[1]] = query_emb.astype('float32')
        query_emb = padded
    else:
        query_emb = query_emb[:, :384].astype('float32')
    
    faiss.normalize_L2(query_emb)
    scores, indices = index.search(query_emb, top_k)
    
    return [
        {"candidate_id": candidate_ids[i], "score": float(scores[0][rank])}
        for rank, i in enumerate(indices[0])
    ]


def main():
    print("Loading profiles...")
    candidate_ids, texts = load_profiles(PROFILES_PATH)
    print(f"Loaded {len(texts)} profiles")

    print("Generating embeddings (TF-IDF)...")
    embeddings = build_embeddings(texts)
    print(f"Embeddings shape: {embeddings.shape}")
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"Saved embeddings -> {EMBEDDINGS_PATH}")

    print("Building FAISS index...")
    index = build_index(embeddings.copy())
    faiss.write_index(index, str(INDEX_PATH))
    print(f"Saved FAISS index -> {INDEX_PATH}  ({index.ntotal} vectors)")

    # Test retrieval
    query = """
Need machine learning engineer
with Python and recommendation systems
experience.
"""
    print(f"\nTest query: {query.strip()}")
    print("-" * 50)

    # Rebuild vectorizer for query encoding (in real scenario, save it)
    vectorizer = TfidfVectorizer(
        max_features=384,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True
    )
    vectorizer.fit(texts)  # Fit on training texts
    
    results = search(query, embeddings, vectorizer, index, candidate_ids, top_k=5)
    
    for rank, r in enumerate(results, 1):
        print(f"  #{rank}  {r['candidate_id']}  score={r['score']:.4f}")


if __name__ == "__main__":
    main()
