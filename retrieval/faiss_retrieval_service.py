"""
retrieval/faiss_retrieval_service.py

Production-ready FAISS retrieval service.
Pre-loads index and vectorizer for instant queries.
"""

import json
import pathlib
import numpy as np
import faiss
import pickle
import time
from sklearn.feature_extraction.text import HashingVectorizer

class FAISSRetriever:
    def __init__(self, index_path="data/faiss_index.bin", 
                 embeddings_path="data/candidate_embeddings.npy",
                 profiles_path="data/candidate_profiles.json"):
        self.index_path = pathlib.Path(index_path)
        self.embeddings_path = pathlib.Path(embeddings_path)
        self.profiles_path = pathlib.Path(profiles_path)
        
        # Load data
        self._load_profiles()
        self._load_index()
        self._setup_vectorizer()
    
    def _load_profiles(self):
        with open(self.profiles_path, encoding="utf-8") as f:
            data = json.load(f)
        self.candidate_ids = [d["candidate_id"] for d in data]
        self.profiles = {d["candidate_id"]: d["profile_text"] for d in data}
    
    def _load_index(self):
        self.index = faiss.read_index(str(self.index_path))
    
    def _setup_vectorizer(self):
        """Create vectorizer (stateless, no fitting needed)"""
        self.vectorizer = HashingVectorizer(
            n_features=384,
            norm='l2',
            alternate_sign=False,
            dtype=np.float32
        )
    
    def search(self, query: str, top_k: int = 5):
        """Search and return top-k candidates"""
        query_emb = self.vectorizer.transform([query]).toarray().astype('float32')
        faiss.normalize_L2(query_emb)
        scores, indices = self.index.search(query_emb, top_k)
        
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            cand_id = self.candidate_ids[idx]
            results.append({
                "rank": rank,
                "candidate_id": cand_id,
                "score": float(score),
                "headline": self.profiles[cand_id].split('\n')[1] if '\n' in self.profiles[cand_id] else ""
            })
        return results


def main():
    print("Initializing FAISS Retriever...")
    t1 = time.time()
    retriever = FAISSRetriever()
    init_time = time.time() - t1
    print(f"[OK] Initialized in {init_time*1000:.2f}ms\n")
    
    # Test queries
    queries = [
        "machine learning engineer Python recommendation systems",
        "frontend react developer",
        "data scientist SQL"
    ]
    
    for query in queries:
        print(f"Query: {query}")
        t1 = time.time()
        results = retriever.search(query, top_k=3)
        search_time = (time.time() - t1) * 1000
        
        for r in results:
            print(f"  {r['rank']}. {r['candidate_id']} (score={r['score']:.4f})")
        print(f"  Time: {search_time:.2f}ms\n")


if __name__ == "__main__":
    main()
