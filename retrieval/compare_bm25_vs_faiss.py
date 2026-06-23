"""
retrieval/compare_bm25_vs_faiss.py

Detailed comparison of BM25 (keyword) vs FAISS (semantic) retrieval.
Shows what each method catches and misses.
"""

import json
import pickle
import pathlib
import numpy as np
import faiss
from sklearn.feature_extraction.text import HashingVectorizer


def load_bm25_results(query: str, top_k: int = 10):
    """Load BM25 index and search"""
    bm25_index_path = pathlib.Path("data/bm25_index.pkl")
    bm25_candidates_path = pathlib.Path("data/bm25_candidates.pkl")
    
    with open(bm25_index_path, 'rb') as f:
        bm25 = pickle.load(f)
    with open(bm25_candidates_path, 'rb') as f:
        candidate_ids = pickle.load(f)
    
    # Simple tokenize
    query_tokens = query.lower().split()
    scores = bm25.get_scores(query_tokens)
    
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    
    results = []
    for rank, idx in enumerate(top_indices, 1):
        results.append({
            'rank': rank,
            'candidate_id': candidate_ids[idx],
            'score': float(scores[idx])
        })
    
    return results


def load_faiss_results(query: str, top_k: int = 10):
    """Load FAISS index and search"""
    faiss_index_path = pathlib.Path("data/faiss_index.bin")
    profiles_path = pathlib.Path("data/candidate_profiles.json")
    
    index = faiss.read_index(str(faiss_index_path))
    
    with open(profiles_path, encoding="utf-8") as f:
        data = json.load(f)
    candidate_ids = [d["candidate_id"] for d in data]
    
    vectorizer = HashingVectorizer(
        n_features=384,
        norm='l2',
        alternate_sign=False,
        dtype=np.float32
    )
    
    query_emb = vectorizer.transform([query]).toarray().astype('float32')
    faiss.normalize_L2(query_emb)
    scores, indices = index.search(query_emb, top_k)
    
    results = []
    for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
        results.append({
            'rank': rank,
            'candidate_id': candidate_ids[idx],
            'score': float(score)
        })
    
    return results


def get_profile(candidate_id: str) -> dict:
    """Get candidate profile"""
    profiles_path = pathlib.Path("data/candidate_profiles.json")
    with open(profiles_path, encoding="utf-8") as f:
        data = json.load(f)
    
    for d in data:
        if d['candidate_id'] == candidate_id:
            lines = d['profile_text'].split('\n')
            headline = lines[1] if len(lines) > 1 else ""
            return {'headline': headline, 'profile': d['profile_text']}
    
    return {'headline': 'N/A', 'profile': ''}


def analyze_query(query: str):
    """Analyze results for a query"""
    print("=" * 100)
    print(f"Query: '{query}'")
    print("=" * 100)
    
    bm25_results = load_bm25_results(query, top_k=10)
    faiss_results = load_faiss_results(query, top_k=10)
    
    bm25_ids = {r['candidate_id']: r for r in bm25_results}
    faiss_ids = {r['candidate_id']: r for r in faiss_results}
    
    # Extract keywords from query
    keywords = query.lower().split()
    print(f"\nKeywords: {keywords}")
    print()
    
    # Show top 5 for each
    print(f"{'BM25 Top 5 (Keyword Matching)':<50} {'FAISS Top 5 (Semantic)':<50}")
    print("-" * 100)
    
    for i in range(5):
        bm25_r = bm25_results[i] if i < len(bm25_results) else None
        faiss_r = faiss_results[i] if i < len(faiss_results) else None
        
        bm25_str = f"{i+1}. {bm25_r['candidate_id']} ({bm25_r['score']:.2f})" if bm25_r else ""
        faiss_str = f"{i+1}. {faiss_r['candidate_id']} ({faiss_r['score']:.4f})" if faiss_r else ""
        
        print(f"{bm25_str:<50} {faiss_str:<50}")
    
    # Detailed analysis
    print("\n" + "=" * 100)
    print("DETAILED COMPARISON")
    print("=" * 100)
    
    # BM25 explanations
    print("\nBM25 (Keyword Matching):")
    print("-" * 100)
    for i, result in enumerate(bm25_results[:5], 1):
        profile = get_profile(result['candidate_id'])
        headline = profile['headline'].replace('Headline: ', '')
        
        # Find matching keywords
        profile_lower = profile['profile'].lower()
        matched_keywords = [kw for kw in keywords if kw in profile_lower]
        
        print(f"{i}. {result['candidate_id']} (score={result['score']:.2f})")
        print(f"   Role: {headline}")
        print(f"   Matched keywords: {matched_keywords}")
        print()
    
    # FAISS explanations
    print("\nFAISS (Semantic Matching):")
    print("-" * 100)
    for i, result in enumerate(faiss_results[:5], 1):
        profile = get_profile(result['candidate_id'])
        headline = profile['headline'].replace('Headline: ', '')
        
        # Why semantic match?
        print(f"{i}. {result['candidate_id']} (score={result['score']:.4f})")
        print(f"   Role: {headline}")
        print(f"   Semantic reason: Related to query concepts")
        print()
    
    # Overlap analysis
    print("\n" + "=" * 100)
    print("AGREEMENT ANALYSIS")
    print("=" * 100)
    
    bm25_top5 = set(r['candidate_id'] for r in bm25_results[:5])
    faiss_top5 = set(r['candidate_id'] for r in faiss_results[:5])
    
    overlap = bm25_top5 & faiss_top5
    bm25_only = bm25_top5 - faiss_top5
    faiss_only = faiss_top5 - bm25_top5
    
    print(f"\nBoth methods agree (Top 5): {len(overlap)} candidates")
    for cid in overlap:
        bm25_rank = next(r['rank'] for r in bm25_results if r['candidate_id'] == cid)
        faiss_rank = next(r['rank'] for r in faiss_results if r['candidate_id'] == cid)
        print(f"  {cid}: BM25 rank {bm25_rank}, FAISS rank {faiss_rank}")
    
    print(f"\nBM25 only (Top 5): {len(bm25_only)} candidates")
    for cid in bm25_only:
        rank = next(r['rank'] for r in bm25_results if r['candidate_id'] == cid)
        print(f"  {cid} (rank {rank}): Has exact keywords")
    
    print(f"\nFAISS only (Top 5): {len(faiss_only)} candidates")
    for cid in faiss_only:
        rank = next(r['rank'] for r in faiss_results if r['candidate_id'] == cid)
        print(f"  {cid} (rank {rank}): Semantic similarity")
    
    print()


def main():
    print("\n")
    print("=" * 100)
    print(" BM25 vs FAISS: Why You Need Both ".center(100))
    print("=" * 100)
    print()
    
    test_queries = [
        "Python SQL Machine Learning",
        "Vector Search Engineer",
        "frontend react developer",
        "recommendation systems"
    ]
    
    for query in test_queries:
        analyze_query(query)
        print()


if __name__ == "__main__":
    main()
