@echo off
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

echo Installing dependencies...
%PY% -m pip install sentence-transformers faiss-cpu rank-bm25 --quiet

echo.
echo === FAISS Dense Retrieval ===
%PY% retrieval\faiss_search.py

echo.
echo === BM25 Keyword Retrieval ===
%PY% retrieval\bm25_search.py

echo.
echo === Hybrid RRF Search ===
%PY% retrieval\hybrid_search.py
