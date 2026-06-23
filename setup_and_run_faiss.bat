@echo off
echo ========================================
echo FAISS Embeddings and Retrieval Setup
echo ========================================
echo.

echo Step 1: Install dependencies
echo ----------------------------
echo pip install sentence-transformers faiss-cpu
echo.

echo Step 2: Generate embeddings and build FAISS index
echo --------------------------------------------------
echo python retrieval\faiss_search.py
echo.

echo Step 3: Expected output files
echo -------------------------------
echo - data\candidate_embeddings.npy (50, 384)
echo - data\faiss_index.bin
echo.

echo Step 4: Test retrieval output will show
echo -----------------------------------------
echo Top 5 matches for query:
echo "Need machine learning engineer"
echo "with Python and recommendation systems"
echo "experience."
echo.

echo To run the complete workflow:
echo 1. Open command prompt in this directory
echo 2. Run: pip install sentence-transformers faiss-cpu
echo 3. Run: python retrieval\faiss_search.py
echo.

pause