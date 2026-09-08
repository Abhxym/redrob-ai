"""
retrieval/hybrid_retrieval.py

Hybrid Retrieval using RRF (Reciprocal Rank Fusion).

Strategy:
1. Get FAISS Top 50 (semantic similarity)
2. Get BM25 Top 50 (keyword matching)
3. Apply RRF: score += 1 / (60 + rank)
4. Combine and return Top 100 candidates

Why This Works:
- BM25 catches exact terms: "NDCG" → finds "NDCG metrics"
- FAISS catches semantics: "Vector Retrieval" → finds "Embedding Search"
- RRF combines both signals for better ranking
"""

import json
import pathlib
import pickle
import time
import numpy as np
import faiss
from sklearn.feature_extraction.text import HashingVectorizer
from collections import defaultdict


class SimpleBM25:
    """Simple BM25 implementation (copied from bm25_search.py)"""
    def __init__(self, corpus, k1=1.5, b=0.75):
        import math
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
        
        # Convert to IDF scores
        for word in self.idf:
            self.idf[word] = (
                math.log(self.corpus_size - self.idf[word] + 0.5) - 
                math.log(self.idf[word] + 0.5)
            )
        
        self.corpus = corpus
    
    def get_scores(self, query):
        scores = [0.0] * self.corpus_size
        for q_term in query:
            if q_term not in self.idf:
                continue
            idf = self.idf[q_term]
            for doc_idx, doc in enumerate(self.corpus):
                freq = doc.count(q_term)
                if freq == 0:
                    continue
                norm = 1 - self.b + self.b * (len(doc) / self.avgdl)
                scores[doc_idx] += idf * (freq * (self.k1 + 1)) / (freq + self.k1 * norm)
        return scores


class HybridRetriever:
    """
    Hybrid retrieval system combining BM25 and FAISS with RRF.
    """
    
    def __init__(self, 
                 profiles_path="data/candidate_profiles.json",
                 faiss_index_path="data/faiss_index.bin",
                 bm25_index_path="data/bm25_index.pkl",
                 bm25_candidates_path="data/bm25_candidates.pkl"):
        
        print("Initializing Hybrid Retriever...")
        
        # Load profiles
        self.profiles_path = pathlib.Path(profiles_path)
        with open(self.profiles_path, encoding="utf-8") as f:
            data = json.load(f)
        self.candidate_ids = [d["candidate_id"] for d in data]
        self.profiles = {d["candidate_id"]: d for d in data}
        
        # Load FAISS
        print("  Loading FAISS index...")
        self.faiss_index = faiss.read_index(faiss_index_path)
        self.vectorizer = HashingVectorizer(
            n_features=384, 
            norm='l2', 
            alternate_sign=False, 
            dtype=np.float32
        )
        
        # Load BM25 — use a custom Unpickler to handle the case where the index
        # was pickled with SimpleBM25 bound to __main__ (i.e. bm25_search.py run
        # as a script) rather than to retrieval.hybrid_retrieval.
        print("  Loading BM25 index...")
        
        class _BM25Unpickler(pickle.Unpickler):
            """Remaps __main__.SimpleBM25 → local SimpleBM25."""
            def find_class(self, module, name):
                if name == 'SimpleBM25':
                    return SimpleBM25
                return super().find_class(module, name)
        
        with open(bm25_index_path, 'rb') as f:
            self.bm25 = _BM25Unpickler(f).load()
        with open(bm25_candidates_path, 'rb') as f:
            self.bm25_candidate_ids = pickle.load(f)
        
        print("  Hybrid Retriever ready!")
    
    def get_faiss_top50(self, query: str) -> list:
        """Get top 50 candidates from FAISS semantic search"""
        query_emb = self.vectorizer.transform([query]).toarray().astype('float32')
        faiss.normalize_L2(query_emb)
        scores, indices = self.faiss_index.search(query_emb, 50)
        
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            results.append({
                'candidate_id': self.candidate_ids[idx],
                'faiss_rank': rank,
                'faiss_score': float(score)
            })
        return results
    
    def get_bm25_top50(self, query: str) -> list:
        """Get top 50 candidates from BM25 keyword search"""
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top 50 indices
        top_indices = sorted(range(len(scores)), 
                           key=lambda i: scores[i], 
                           reverse=True)[:50]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            results.append({
                'candidate_id': self.bm25_candidate_ids[idx],
                'bm25_rank': rank,
                'bm25_score': float(scores[idx])
            })
        return results
    
    def apply_rrf(self, faiss_results: list, bm25_results: list) -> list:
        """
        Apply RRF (Reciprocal Rank Fusion) with formula: score += 1 / (60 + rank)
        
        Args:
            faiss_results: FAISS top 50 results
            bm25_results: BM25 top 50 results
            
        Returns:
            Combined results with RRF scores, top 100
        """
        rrf_scores = defaultdict(lambda: {
            'rrf_score': 0.0,
            'faiss_rank': None,
            'faiss_score': None,
            'bm25_rank': None,
            'bm25_score': None,
            'in_faiss': False,
            'in_bm25': False
        })
        
        # Add FAISS scores
        for result in faiss_results:
            cand_id = result['candidate_id']
            rank = result['faiss_rank']
            
            # RRF Formula: score += 1 / (60 + rank)
            rrf_scores[cand_id]['rrf_score'] += 1.0 / (60 + rank)
            rrf_scores[cand_id]['faiss_rank'] = rank
            rrf_scores[cand_id]['faiss_score'] = result['faiss_score']
            rrf_scores[cand_id]['in_faiss'] = True
        
        # Add BM25 scores
        for result in bm25_results:
            cand_id = result['candidate_id']
            rank = result['bm25_rank']
            
            # RRF Formula: score += 1 / (60 + rank)
            rrf_scores[cand_id]['rrf_score'] += 1.0 / (60 + rank)
            rrf_scores[cand_id]['bm25_rank'] = rank
            rrf_scores[cand_id]['bm25_score'] = result['bm25_score']
            rrf_scores[cand_id]['in_bm25'] = True
        
        # Sort by RRF score and take top 100
        sorted_results = sorted(
            rrf_scores.items(), 
            key=lambda x: x[1]['rrf_score'], 
            reverse=True
        )[:100]
        
        # Format results
        final_results = []
        for rank, (cand_id, scores) in enumerate(sorted_results, 1):
            profile = self.profiles.get(cand_id, {})
            headline = self._extract_headline(profile.get('profile_text', ''))
            
            final_results.append({
                'rank': rank,
                'candidate_id': cand_id,
                'rrf_score': scores['rrf_score'],
                'headline': headline,
                'faiss_rank': scores['faiss_rank'],
                'faiss_score': scores['faiss_score'],
                'bm25_rank': scores['bm25_rank'],
                'bm25_score': scores['bm25_score'],
                'in_faiss': scores['in_faiss'],
                'in_bm25': scores['in_bm25'],
                'source': self._get_source(scores)
            })
        
        return final_results
    
    def _extract_headline(self, profile_text: str) -> str:
        """Extract headline from profile text"""
        lines = profile_text.split('\n')
        for line in lines:
            if line.startswith('Headline:'):
                return line.replace('Headline: ', '').strip()
        return 'N/A'
    
    def _get_source(self, scores: dict) -> str:
        """Determine source of ranking"""
        if scores['in_faiss'] and scores['in_bm25']:
            return 'BOTH'
        elif scores['in_faiss']:
            return 'FAISS'
        elif scores['in_bm25']:
            return 'BM25'
        else:
            return 'NONE'
    
    def search(self, query: str) -> dict:
        """
        Main search function: Returns top 100 candidates using hybrid retrieval
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary with results and metadata
        """
        start_time = time.time()
        
        print(f"\nQuery: '{query}'")
        print("-" * 80)
        
        # Step 1: Get FAISS top 50
        t1 = time.time()
        faiss_results = self.get_faiss_top50(query)
        faiss_time = (time.time() - t1) * 1000
        print(f"FAISS Top 50: {faiss_time:.2f}ms")
        
        # Step 2: Get BM25 top 50
        t1 = time.time()
        bm25_results = self.get_bm25_top50(query)
        bm25_time = (time.time() - t1) * 1000
        print(f"BM25 Top 50:  {bm25_time:.2f}ms")
        
        # Step 3: Apply RRF and get top 100
        t1 = time.time()
        hybrid_results = self.apply_rrf(faiss_results, bm25_results)
        rrf_time = (time.time() - t1) * 1000
        print(f"RRF Fusion:   {rrf_time:.2f}ms")
        
        total_time = (time.time() - start_time) * 1000
        print(f"Total Time:   {total_time:.2f}ms")
        
        # Analyze results
        faiss_only = sum(1 for r in hybrid_results if r['source'] == 'FAISS')
        bm25_only = sum(1 for r in hybrid_results if r['source'] == 'BM25')
        both = sum(1 for r in hybrid_results if r['source'] == 'BOTH')
        
        print(f"\nResult Sources (Top 100):")
        print(f"  FAISS only: {faiss_only}")
        print(f"  BM25 only:  {bm25_only}")
        print(f"  Both:       {both}")
        print(f"  Total:      {len(hybrid_results)}")
        
        return {
            'query': query,
            'results': hybrid_results,
            'metadata': {
                'total_results': len(hybrid_results),
                'faiss_time_ms': faiss_time,
                'bm25_time_ms': bm25_time,
                'rrf_time_ms': rrf_time,
                'total_time_ms': total_time,
                'source_counts': {
                    'faiss_only': faiss_only,
                    'bm25_only': bm25_only,
                    'both': both
                }
            }
        }


def main():
    """Demo the hybrid retrieval system"""
    
    print("=" * 100)
    print("HYBRID RETRIEVAL SYSTEM")
    print("RRF Formula: score += 1 / (60 + rank)")
    print("Input: FAISS Top 50 + BM25 Top 50")
    print("Output: Top 100 Candidates")
    print("=" * 100)
    
    # Initialize
    retriever = HybridRetriever()
    
    # Test queries demonstrating BM25 vs FAISS strengths
    test_queries = [
        {
            'query': 'NDCG metrics evaluation',
            'explanation': 'BM25 should catch exact "NDCG" term'
        },
        {
            'query': 'Vector Retrieval systems',
            'explanation': 'FAISS should find "Embedding Search" semantically'
        },
        {
            'query': 'Python machine learning engineer',
            'explanation': 'Both methods should contribute'
        },
        {
            'query': 'recommendation systems ranking',
            'explanation': 'Perfect case: exact match + semantic'
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*100}")
        print(f"TEST {i}: {test_case['explanation']}")
        print(f"{'='*100}")
        
        result = retriever.search(test_case['query'])
        
        # Show top 10 results
        print(f"\nTop 10 Results:")
        print("-" * 100)
        print(f"{'Rank':<5} {'Candidate':<15} {'RRF Score':<10} {'Source':<8} {'Headline':<50}")
        print("-" * 100)
        
        for r in result['results'][:10]:
            headline_short = r['headline'][:47] + "..." if len(r['headline']) > 50 else r['headline']
            print(f"{r['rank']:<5} {r['candidate_id']:<15} {r['rrf_score']:<10.4f} "
                  f"{r['source']:<8} {headline_short:<50}")
        
        print(f"\nBreakdown:")
        metadata = result['metadata']
        print(f"  Sources: {metadata['source_counts']['both']} both, "
              f"{metadata['source_counts']['faiss_only']} FAISS only, "
              f"{metadata['source_counts']['bm25_only']} BM25 only")
        print(f"  Performance: {metadata['total_time_ms']:.2f}ms total")
        
        print("\n")


if __name__ == "__main__":
    main()