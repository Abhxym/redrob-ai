"""
RedRob AI Recruiter — FastAPI Backend
Exposes the submission ranking pipeline (generate_submission.rank) over HTTP for the frontend:
BM25 + FAISS -> RRF -> multi-signal scoring with dynamic weights -> cross-encoder rerank.
"""
import sys
import os

# Ensure the project root is on the path and is the working directory, since the
# pipeline resolves data paths relative to it.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import pickle
import threading
import time

import generate_submission as pipeline
from preprocessing.build_candidate_profiles import build_profile_text as format_profile


# ─── Warm-up ──────────────────────────────────────────────────────────────────
# Loading 100k candidates, the indexes and both models takes a while, so do it once
# in the background at startup instead of on the first request.

_warm = {"state": "starting", "error": None, "seconds": None}
_rank_lock = threading.Lock()


def _warm_up():
    t0 = time.perf_counter()
    try:
        _warm["state"] = "loading"
        pipeline.load_state()
        pipeline._get_model()
        pipeline._get_ce_model()
        _warm["state"] = "ready"
    except Exception as exc:  # surfaced through /api/health
        _warm["state"] = "error"
        _warm["error"] = str(exc)
    _warm["seconds"] = round(time.perf_counter() - t0, 1)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=_warm_up, daemon=True).start()
    yield


app = FastAPI(
    title="RedRob AI Recruiter API",
    description="Candidate ranking: hybrid BM25+FAISS retrieval (RRF), multi-signal scoring and cross-encoder re-ranking. No LLM.",
    version="2.0.0",
    lifespan=lifespan,
)

# Allow the Vite dev server and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────

class RankRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, description="Job description text")
    top_k: Optional[int] = Field(default=10, ge=1, le=100, description="Number of top candidates")


class ScoreBreakdown(BaseModel):
    semantic: float
    skills: float
    experience: float
    behavior: float
    career: float
    cross_encoder: Optional[float] = None


class CandidateResult(BaseModel):
    rank: int
    candidate_id: str
    final_score: float
    feature_score: float
    scores: ScoreBreakdown
    reasoning: list[str]
    headline: str
    current_title: str
    location: str
    experience_years: float
    open_to_work: bool
    notice_days: Optional[int] = None
    matched_skills: list[str]


class RankResponse(BaseModel):
    jd_snippet: str
    total_evaluated: int
    results: list[CandidateResult]
    pipeline_info: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    candidates_loaded: int
    warm_state: str
    warm_seconds: Optional[float] = None
    error: Optional[str] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

_corpus_size = None


def _indexed_count() -> int:
    """Corpus size from the cached id list, without loading the full dataset."""
    global _corpus_size
    if _corpus_size is None:
        try:
            with open(pipeline.IDS_CACHE, "rb") as f:
                _corpus_size = len(pickle.load(f))
        except Exception:
            return 0
    return _corpus_size


def _require_ready():
    if _warm["state"] == "error":
        raise HTTPException(status_code=500, detail=f"Pipeline failed to load: {_warm['error']}")
    if _warm["state"] != "ready":
        raise HTTPException(status_code=503, detail="Models and indexes are still loading — try again shortly.")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """API health, corpus size, and whether the pipeline has finished warming up."""
    return HealthResponse(
        status="ok",
        version=app.version,
        candidates_loaded=_indexed_count(),
        warm_state=_warm["state"],
        warm_seconds=_warm["seconds"],
        error=_warm["error"],
    )


@app.post("/api/rank", response_model=RankResponse, tags=["Ranking"])
def rank_candidates(req: RankRequest):
    """
    Run the full ranking pipeline on the provided job description.
    Returns top-k ranked candidates with the score breakdown and factual reasoning.
    """
    _require_ready()
    try:
        with _rank_lock:
            t0 = time.perf_counter()
            rows, meta = pipeline.rank(req.jd_text)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(exc)}")

    cand_map = pipeline.load_state()["cand_map"]
    results: list[CandidateResult] = []
    for r in rows[: req.top_k]:
        p = cand_map[r["candidate_id"]]["profile"]
        results.append(
            CandidateResult(
                rank=r["rank"],
                candidate_id=r["candidate_id"],
                final_score=r["score"],
                feature_score=r.get("feature_score", r["score"]),
                scores=ScoreBreakdown(
                    semantic=r["semantic_score"],
                    skills=r["skill_score"],
                    experience=r["exp_score"],
                    behavior=r["behavior_score"],
                    career=r["career_score"],
                    cross_encoder=r.get("ce_score"),
                ),
                reasoning=[item.strip() for item in r["reasoning"].split("|") if item.strip()],
                headline=p.get("headline", ""),
                current_title=r["current_title"],
                location=r["location"],
                experience_years=r["years_exp"],
                open_to_work=r["open_to_work"] == "Yes",
                notice_days=r["notice_days"],
                matched_skills=[s.strip() for s in r["matched_skills"].split(",") if s.strip()],
            )
        )

    weights = meta["weights"]
    jd_snippet = req.jd_text.strip()[:120] + ("…" if len(req.jd_text.strip()) > 120 else "")

    return RankResponse(
        jd_snippet=jd_snippet,
        total_evaluated=meta["retrieved"],
        results=results,
        pipeline_info={
            "retrieval": "BM25 + FAISS (RRF fusion)",
            "reranker": pipeline.CE_MODEL_NAME if meta["ce_applied"] else None,
            "weights": {
                "semantic": weights["semantic_score"],
                "skills": weights["skill_score"],
                "experience": weights["experience_score"],
                "behavior": weights["behavior_score"],
                "career": weights["career_score"],
            },
            "ce_blend": meta["ce_blend"] if meta["ce_applied"] else None,
            "jd_type": meta["jd_type"],
            "jd_skills": meta["jd_requirements"].get("skills", []),
            "jd_experience": meta["jd_requirements"].get("experience"),
            "corpus_size": meta["corpus_size"],
            "timings": meta["timings"],
            "latency": f"{elapsed_ms / 1000:.1f}s",
            "cost": "$0 (no LLM)",
        },
    )


@app.get("/api/candidates/{candidate_id}", tags=["Candidates"])
def get_candidate(candidate_id: str):
    """Returns the full profile for a specific candidate."""
    _require_ready()
    c = pipeline.load_state()["cand_map"].get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return {"candidate_id": candidate_id, "profile_text": format_profile(c)}
