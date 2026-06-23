"""
retrieval/hybrid_search.py

Hybrid search combining BM25 (keyword) and FAISS (semantic) using RRF.
RRF = Reciprocal Rank Fusion: combines rankings from multiple systems.
"""

import json
import pathlib
import time
import math
import numpy as np
import faiss
from sklearn.feature_extraction.text import HashingVectorizer


class SimpleBM25:
    """Simple BM25 implementation"""
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.avgdl = sum(len(d) for d in corpus) / len(corpus)
        self.idf = self._compute_idf(corpus)
    
    def _compute_idf(self, corpus):
        idf = {}
        N = len(corpus)
        for doc in corpus:
            unique_words = set(doc)
            for word in unique_words:
                idf[word] = idf.get(word, 0) + 1
        
        for word in idf:
            idf[word] = math.log(N - idf[word] + 0.5) - math.log(idf[word] + 0.5)
        return idf
    
    def get_scores(self, query):
        scores = [0.0] * len(self.corpus)
        for i, doc in enumerate(self.corpus):
            for q_term in query:
                if q_term not in self.idf:
                    continue
                freq = doc.count(q_term)
                norm = 1 - self.b + self.b * len(doc) / self.avgdl
                scores[i] += self.idf[q_term] * (freq * (self.k1 + 1)) / (freq + self.k1 * norm)
        return scores


class HybridSearcher:
    def __init__(self, profiles_path="data/candidate_profiles.json",
                 index_path="data/faiss_index.bin"):
        self.profiles_path = pathlib.Path(profiles_path)
        self.index_path = pathlib.Path(index_path)
        
        # Load profiles
        with open(self.profiles_path, encoding="utf-8") as f:
            data = json.load(f)
        self.candidate_ids = [d["candidate_id"] for d in data]
        self.texts = [d["profile_text"] for d in data]
        
        # Build BM25
        self.bm25 = SimpleBM25([self._tokenize(t) for t in self.texts])
        
        # Load FAISS
        self.faiss_index = faiss.read_index(str(self.index_path))
        self.vectorizer = HashingVectorizer(n_features=384, norm='l2', 
                                            alternate_sign=False, dtype=np.float32)
    
    def _tokenize(self, text: str) -> list:
        return text.lower().split()
    
    def search(self, query: str, top_k: int = 5, k1_weight: float = 0.5, 
               k2_weight: float = 0.5) -> list:
        """
        Hybrid search using RRF (Reciprocal Rank Fusion)
        
        Args:
            query: Search query string
            top_k: Number of results to return
            k1_weight: Weight for BM25 (0-1)
            k2_weight: Weight for FAISS (0-1)
        """
        # Get BM25 results
        bm25_scores = self.bm25.get_scores(self._tokenize(query))
        
        # Get FAISS results
        query_emb = self.vectorizer.transform([query]).toarray().astype('float32')
        faiss.normalize_L2(query_emb)
        faiss_scores, faiss_indices_arr = self.faiss_index.search(query_emb, len(self.candidate_ids))
        faiss_scores = faiss_scores[0]
        faiss_indices = faiss_indices_arr[0]  # Get first (only) result
        
        # RRF formula: score = k1_weight / (rank_bm25 + 1) + k2_weight / (rank_faiss + 1)
        rrf_scores = {}
        
        for i, cand_id in enumerate(self.candidate_ids):
            bm25_rank = sorted(range(len(bm25_scores)), 
                              key=lambda j: bm25_scores[j], reverse=True).index(i)
            faiss_rank = int(list(faiss_indices).index(i))
            
            rrf_score = (k1_weight / (bm25_rank + 1) + 
                        k2_weight / (faiss_rank + 1))
            rrf_scores[cand_id] = {
                'rrf_score': rrf_score,
                'bm25_score': bm25_scores[i],
                'faiss_score': faiss_scores[i],
                'bm25_rank': bm25_rank + 1,
                'faiss_rank': faiss_rank + 1
            }
        
        # Sort by RRF score
        sorted_results = sorted(rrf_scores.items(), 
                               key=lambda x: x[1]['rrf_score'], 
                               reverse=True)[:top_k]
        
        results = []
        for rank, (cand_id, scores) in enumerate(sorted_results, 1):
            results.append({
                'rank': rank,
                'candidate_id': cand_id,
                'rrf_score': scores['rrf_score'],
                'bm25_score': scores['bm25_score'],
                'faiss_score': scores['faiss_score'],
                'bm25_rank': scores['bm25_rank'],
                'faiss_rank': scores['faiss_rank']
            })
        
        return results


def main():
    print("=" * 90)
    print("HYBRID SEARCH: BM25 + FAISS with RRF (Reciprocal Rank Fusion)")
    print("=" * 90)
    
    t1 = time.time()
    searcher = HybridSearcher()
    init_time = (time.time() - t1) * 1000
    print(f"\n[OK] Initialized ({init_time:.2f}ms)\n")
    
    # Test queries
    test_queries = [
        ("Vector Search Engineer", 0.5, 0.5),
        ("machine learning engineer Python", 0.4, 0.6),
        ("frontend react developer", 0.6, 0.4),
        ("recommendation systems", 0.3, 0.7),
    ]
    
    for query, bm25_w, faiss_w in test_queries:
        print(f"Query: '{query}'")
        print(f"Weights: BM25={bm25_w} | FAISS={faiss_w}")
        print("-" * 90)
        
        t1 = time.time()
        results = searcher.search(query, top_k=5, k1_weight=bm25_w, k2_weight=faiss_w)
        search_time = (time.time() - t1) * 1000
        
        # Header
        print(f"{'Rank':<5} {'Candidate':<15} {'RRF':<8} {'BM25':<8} {'BM25R':<6} {'FAISS':<8} {'FAISSR':<6}")
        print("-" * 90)
        
        for r in results:
            print(f"{r['rank']:<5} {r['candidate_id']:<15} "
                  f"{r['rrf_score']:<8.4f} {r['bm25_score']:<8.2f} {r['bm25_rank']:<6} "
                  f"{r['faiss_score']:<8.4f} {r['faiss_rank']:<6}")
        
        print(f"Search time: {search_time:.2f}ms\n")


if __name__ == "__main__":
    main()
