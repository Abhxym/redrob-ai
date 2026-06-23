import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def generate_embeddings():
    """Load candidate profiles and generate embeddings"""
    
    # Load candidate profiles
    with open('data/candidate_profiles.json', 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    print(f"Loaded {len(candidates)} candidate profiles")
    
    # Extract profile texts for embedding
    profile_texts = [candidate['profile_text'] for candidate in candidates]
    candidate_ids = [candidate['candidate_id'] for candidate in candidates]
    
    # Load embedding model (all-MiniLM-L6-v2 has dimension 384)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(profile_texts, show_progress_bar=True)
    
    # Print shape
    print(f"Embeddings shape: {embeddings.shape}")
    
    # Save embeddings
    np.save('data/candidate_embeddings.npy', embeddings)
    print("Saved embeddings to data/candidate_embeddings.npy")
    
    return embeddings, candidate_ids

def build_faiss_index(embeddings):
    """Build and save FAISS index"""
    
    dimension = embeddings.shape[1]
    
    # Create index with inner product similarity (for cosine similarity after L2 normalization)
    index = faiss.IndexFlatIP(dimension)
    
    # Normalize vectors for cosine similarity
    faiss.normalize_L2(embeddings)
    
    # Add embeddings to index
    index.add(embeddings)
    
    # Save index
    faiss.write_index(index, "data/faiss_index.bin")
    print(f"Saved FAISS index to data/faiss_index.bin with {index.ntotal} vectors")
    
    return index

def test_retrieval(index, candidate_ids):
    """Test retrieval with a sample query"""
    
    # Load embedding model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create test query
    query = """
Need machine learning engineer
with Python and recommendation systems
experience.
"""
    
    print(f"\nTest query: {query}")
    
    # Embed query
    query_embedding = model.encode([query])
    
    # Normalize query embedding
    query_embedding_norm = query_embedding.astype('float32')
    faiss.normalize_L2(query_embedding_norm)
    
    # Search
    k = 5
    scores, indices = index.search(query_embedding_norm, k)
    
    print(f"\nTop {k} matches:")
    print("-" * 50)
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        candidate_id = candidate_ids[idx]
        print(f"{i+1}. Candidate ID: {candidate_id}")
        print(f"   Score: {score:.4f}")
    print("-" * 50)
    
    return scores, indices

def main():
    """Main function to generate embeddings and build FAISS index"""
    
    # Generate embeddings
    embeddings, candidate_ids = generate_embeddings()
    
    # Build FAISS index
    index = build_faiss_index(embeddings)
    
    # Test retrieval
    test_retrieval(index, candidate_ids)

if __name__ == "__main__":
    main()