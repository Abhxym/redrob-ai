"""
retrieval/bm25_search.py

BM25 keyword-based search with persistence.
Tokenizes profile_text.split() and saves index with pickle.
"""

import json
import pathlib
import pickle
import time
from typing import List, Tuple

PROFILES_PATH = pathlib.Path("data/candidate_profiles.json")
BM25_INDEX_PATH = pathlib.Path("data/bm25_index.pkl")
BM25_CANDIDATES_PATH = pathlib.Path("data/bm25_candidates.pkl")


class SimpleBM25:
    """
    BM25 implementation (no external dependency required).
    Implements Okapi BM25 ranking function.
    """
    
    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 index.
        
        Args:
            corpus: List of tokenized documents (List[str])
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size
        
        # Build IDF
        self.idf = {}
        for doc in corpus:
            unique_words = set(doc)
            for word in unique_words:
                self.idf[word] = self.idf.get(word, 0) + 1
        
        # Convert to IDF scores (log odds)
        for word in self.idf:
            self.idf[word] = (
                np.log(self.corpus_size - self.idf[word] + 0.5) - 
                np.log(self.idf[word] + 0.5)
            )
        
        self.corpus = corpus
    
    def get_scores(self, query: List[str]) -> List[float]:
        """
        Calculate BM25 scores for all documents given a query.
        
        Args:
            query: Tokenized query (List[str])
        
        Returns:
            List of scores for each document
        """
        scores = [0.0] * self.corpus_size
        
        for q_term in query:
            if q_term not in self.idf:
                continue
            
            idf = self.idf[q_term]
            
            for doc_idx, doc in enumerate(self.corpus):
                freq = doc.count(q_term)
                if freq == 0:
                    continue
                
                # BM25 formula
                norm = 1 - self.b + self.b * (len(doc) / self.avgdl)
                score = idf * (freq * (self.k1 + 1)) / (freq + self.k1 * norm)
                scores[doc_idx] += score
        
        return scores


import numpy as np


def load_profiles(path: pathlib.Path) -> Tuple[List[str], List[str]]:
    """Load candidate profiles"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    ids = [d["candidate_id"] for d in data]
    texts = [d["profile_text"] for d in data]
    return ids, texts


def tokenize(text: str) -> List[str]:
    """Simple tokenization: split and lowercase"""
    return text.lower().split()


def build_bm25_index(texts: List[str]) -> SimpleBM25:
    """Build BM25 index from texts"""
    print("Tokenizing documents...")
    tokenized_docs = [tokenize(text) for text in texts]
    
    print("Building BM25 index...")
    bm25 = SimpleBM25(tokenized_docs)
    
    return bm25


def save_index(bm25: SimpleBM25, candidate_ids: List[str]):
    """Save BM25 index and candidates to pickle"""
    with open(BM25_INDEX_PATH, 'wb') as f:
        pickle.dump(bm25, f)
    print(f"[OK] Saved BM25 index -> {BM25_INDEX_PATH}")
    
    with open(BM25_CANDIDATES_PATH, 'wb') as f:
        pickle.dump(candidate_ids, f)
    print(f"[OK] Saved candidate IDs -> {BM25_CANDIDATES_PATH}")


def load_index() -> Tuple[SimpleBM25, List[str]]:
    """Load BM25 index from pickle"""
    with open(BM25_INDEX_PATH, 'rb') as f:
        bm25 = pickle.load(f)
    
    with open(BM25_CANDIDATES_PATH, 'rb') as f:
        candidate_ids = pickle.load(f)
    
    return bm25, candidate_ids


def search(query: str, bm25: SimpleBM25, candidate_ids: List[str], 
           top_k: int = 10) -> List[dict]:
    """Search using BM25"""
    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)
    
    # Get top-k indices
    top_indices = sorted(range(len(scores)), 
                        key=lambda i: scores[i], 
                        reverse=True)[:top_k]
    
    results = []
    for rank, idx in enumerate(top_indices, 1):
        results.append({
            'rank': rank,
            'candidate_id': candidate_ids[idx],
            'score': float(scores[idx]),
            'tokens': query_tokens
        })
    
    return results


def main():
    print("=" * 80)
    print("BM25 KEYWORD SEARCH")
    print("=" * 80)
    
    # Build or load
    if BM25_INDEX_PATH.exists() and BM25_CANDIDATES_PATH.exists():
        print("\n[OK] Loading existing BM25 index...")
        t1 = time.time()
        bm25, candidate_ids = load_index()
        load_time = (time.time() - t1) * 1000
        print(f"[OK] Loaded in {load_time:.2f}ms")
    else:
        print("\n[OK] Building new BM25 index...")
        t1 = time.time()
        candidate_ids, texts = load_profiles(PROFILES_PATH)
        bm25 = build_bm25_index(texts)
        build_time = (time.time() - t1) * 1000
        print(f"[OK] Built in {build_time:.2f}ms")
        
        # Save
        save_index(bm25, candidate_ids)
    
    # Test queries
    test_queries = [
        "Python SQL Machine Learning",
        "frontend react developer",
        "Vector Search Engineer",
        "recommendation systems",
        "data science sql python"
    ]
    
    print("\n" + "=" * 80)
    print("SEARCH RESULTS (BM25 - Top 10 per query)")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 80)
        
        t1 = time.time()
        results = search(query, bm25, candidate_ids, top_k=10)
        search_time = (time.time() - t1) * 1000
        
        print(f"{'Rank':<6} {'Candidate':<15} {'Score':<12}")
        print("-" * 80)
        for r in results:
            print(f"{r['rank']:<6} {r['candidate_id']:<15} {r['score']:<12.4f}")
        
        print(f"Search time: {search_time:.2f}ms")


if __name__ == "__main__":
    main()
