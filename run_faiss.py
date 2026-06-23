#!/usr/bin/env python
"""
Simple script to run FAISS embeddings generation and retrieval
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to run the existing faiss_search.py
    exec(open('retrieval/faiss_search.py').read())
except Exception as e:
    print(f"Error running faiss_search.py: {e}")
    print("\nCreating a minimal version...")
    
    # Create minimal version
    import json
    import numpy as np
    
    # Load profiles
    with open('data/candidate_profiles.json', 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    print(f"Loaded {len(candidates)} profiles")
    print("To generate embeddings and build FAISS index:")
    print("1. Install dependencies: pip install sentence-transformers faiss-cpu")
    print("2. Run: python retrieval/faiss_search.py")
    print("\nExpected output files:")
    print("- data/candidate_embeddings.npy (shape: (50, 384))")
    print("- data/faiss_index.bin")
    
    # Show what the shape should be
    print(f"\nExpected embeddings shape: ({len(candidates)}, 384) or similar")