import json
import pathlib
import time
import pickle
import numpy as np
import faiss
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from preprocessing.build_candidate_profiles import build_profile_text
from retrieval.faiss_search_fast import build_embeddings_fast, build_index_fast
from retrieval.bm25_search import build_bm25_index, SimpleBM25

CHALLENGE_DATA_JSONL = r"c:\Users\Admin\OneDrive\Desktop\redrob-ai\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
OUT_DIR = pathlib.Path("challenge_data")

def main():
    OUT_DIR.mkdir(exist_ok=True)
    
    print("Loading 100k candidates...")
    t1 = time.time()
    
    candidate_ids = []
    texts = []
    
    with open(CHALLENGE_DATA_JSONL, 'r', encoding='utf-8') as f:
        for line in f:
            cand = json.loads(line)
            candidate_ids.append(cand['candidate_id'])
            texts.append(build_profile_text(cand))
            
    print(f"[OK] Loaded and built text for {len(texts)} candidates in {time.time()-t1:.2f}s")
    
    # 1. Build FAISS
    print("\nBuilding FAISS Fast Embeddings...")
    t1 = time.time()
    embeddings, vectorizer = build_embeddings_fast(texts)
    print(f"[OK] Generated embeddings {embeddings.shape} in {time.time()-t1:.2f}s")
    
    # Save vectorizer if needed (actually it doesn't need fit, so no need to save, but let's save the faiss index and embeddings)
    np.save(OUT_DIR / "candidate_embeddings.npy", embeddings)
    
    print("Building FAISS Index...")
    t1 = time.time()
    index = build_index_fast(embeddings.copy())
    faiss.write_index(index, str(OUT_DIR / "faiss_index.bin"))
    print(f"[OK] Saved FAISS index in {time.time()-t1:.2f}s")
    
    # 2. Build BM25
    print("\nBuilding BM25 Index...")
    t1 = time.time()
    bm25 = build_bm25_index(texts)
    print(f"[OK] Built BM25 in {time.time()-t1:.2f}s")
    
    with open(OUT_DIR / "bm25_index.pkl", 'wb') as f:
        pickle.dump(bm25, f)
    with open(OUT_DIR / "bm25_candidates.pkl", 'wb') as f:
        pickle.dump(candidate_ids, f)
    
    print(f"[OK] Saved BM25 index and candidates to {OUT_DIR}")
    print("\nAll indices built successfully!")

if __name__ == '__main__':
    main()
