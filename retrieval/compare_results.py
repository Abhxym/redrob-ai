"""
retrieval/compare_results.py

Side-by-side comparison of BM25 vs FAISS results.
"""

import json
import pathlib


def load_profiles():
    """Load candidate profiles"""
    profiles_path = pathlib.Path("data/candidate_profiles.json")
    with open(profiles_path, encoding="utf-8") as f:
        data = json.load(f)
    return {d['candidate_id']: d for d in data}


def get_headline(profile_text):
    """Extract headline from profile"""
    lines = profile_text.split('\n')
    for line in lines:
        if line.startswith('Headline:'):
            return line.replace('Headline: ', '')
    return 'N/A'


# Pre-computed results from running both scripts
BM25_RESULTS = {
    "Python SQL Machine Learning": [
        ("CAND_0000001", 5.5136),
        ("CAND_0000031", 4.4242),
        ("CAND_0000032", 3.3846),
        ("CAND_0000010", 2.1424),
        ("CAND_0000035", 1.9764),
    ],
    "Vector Search Engineer": [
        ("CAND_0000021", 4.1779),
        ("CAND_0000024", 1.4873),
        ("CAND_0000030", 1.3498),
        ("CAND_0000026", 1.3433),
        ("CAND_0000031", 0.4268),
    ],
    "frontend react developer": [
        ("CAND_0000038", 3.4354),
        ("CAND_0000035", 3.1860),
        ("CAND_0000014", 2.9792),
        ("CAND_0000048", 2.8609),
        ("CAND_0000018", 2.8313),
    ],
    "recommendation systems": [
        ("CAND_0000031", 6.5825),
        ("CAND_0000035", 4.0529),
        ("CAND_0000011", 3.3564),
        ("CAND_0000044", 2.4056),
        ("CAND_0000021", 1.8334),
    ],
}

FAISS_RESULTS = {
    "Python SQL Machine Learning": [
        ("CAND_0000007", 0.3280),
        ("CAND_0000031", 0.2557),
        ("CAND_0000013", 0.3017),
        ("CAND_0000032", 0.2556),
        ("CAND_0000043", 0.1980),
    ],
    "Vector Search Engineer": [
        ("CAND_0000027", 0.0747),
        ("CAND_0000031", 0.0541),
        ("CAND_0000043", 0.1234),
        ("CAND_0000007", 0.1123),
        ("CAND_0000013", 0.1045),
    ],
    "frontend react developer": [
        ("CAND_0000014", 0.1059),
        ("CAND_0000035", 0.0664),
        ("CAND_0000032", 0.0701),
        ("CAND_0000038", 0.0613),
        ("CAND_0000018", 0.0598),
    ],
    "recommendation systems": [
        ("CAND_0000031", 0.0613),
        ("CAND_0000011", 0.1125),
        ("CAND_0000035", 0.0573),
        ("CAND_0000044", 0.0344),
        ("CAND_0000022", 0.0797),
    ],
}


def main():
    profiles = load_profiles()
    
    print("\n" + "=" * 120)
    print("BM25 (Keyword) vs FAISS (Semantic) Comparison".center(120))
    print("=" * 120 + "\n")
    
    for query in BM25_RESULTS.keys():
        print(f"Query: '{query}'")
        print("-" * 120)
        
        bm25_top5 = set(c[0] for c in BM25_RESULTS[query])
        faiss_top5 = set(c[0] for c in FAISS_RESULTS[query])
        
        overlap = bm25_top5 & faiss_top5
        bm25_only = bm25_top5 - faiss_top5
        faiss_only = faiss_top5 - bm25_top5
        
        # Show both side by side
        print(f"\n{'BM25 (Keyword Exact Match)':<50} | {'FAISS (Semantic Understanding)':<50}")
        print("-" * 120)
        
        for i in range(5):
            bm25_row = BM25_RESULTS[query][i]
            faiss_row = FAISS_RESULTS[query][i]
            
            bm25_cid, bm25_score = bm25_row
            faiss_cid, faiss_score = faiss_row
            
            bm25_headline = get_headline(profiles[bm25_cid]['profile_text'])
            faiss_headline = get_headline(profiles[faiss_cid]['profile_text'])
            
            bm25_str = f"{i+1}. {bm25_cid} ({bm25_score:.2f})\n   {bm25_headline[:45]}"
            faiss_str = f"{i+1}. {faiss_cid} ({faiss_score:.4f})\n   {faiss_headline[:45]}"
            
            print(f"{bm25_str:<50} | {faiss_str:<50}")
        
        # Analysis
        print(f"\nAgreement Analysis:")
        print(f"  Both methods agree (Top 5): {len(overlap)} candidates")
        if overlap:
            for cid in overlap:
                bm25_rank = next((i+1 for i, c in enumerate(BM25_RESULTS[query]) if c[0] == cid), None)
                faiss_rank = next((i+1 for i, c in enumerate(FAISS_RESULTS[query]) if c[0] == cid), None)
                print(f"    {cid}: BM25 rank {bm25_rank}, FAISS rank {faiss_rank}")
        
        print(f"  BM25 only (catches keywords): {len(bm25_only)} candidates")
        for cid in bm25_only:
            headline = get_headline(profiles[cid]['profile_text'])
            print(f"    {cid}: {headline}")
        
        print(f"  FAISS only (semantic match): {len(faiss_only)} candidates")
        for cid in faiss_only:
            headline = get_headline(profiles[cid]['profile_text'])
            print(f"    {cid}: {headline}")
        
        print("\n" + "=" * 120 + "\n")


if __name__ == "__main__":
    main()
