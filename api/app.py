"""
RedRob AI Recruiter — FastAPI Backend
Exposes the ranking pipeline over HTTP for the frontend.
"""
import sys
import os

# Ensure the project root is on the path so imports like `from main import main` work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import json

from main import main as run_pipeline, load_candidates

app = FastAPI(
    title="RedRob AI Recruiter API",
    description="AI-powered candidate ranking system using hybrid BM25+FAISS retrieval with multi-signal scoring.",
    version="1.0.0",
)

# Allow the Vite dev server (port 5173) and any localhost origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────

class RankRequest(BaseModel):
    jd_text: str = Field(..., min_length=20, description="Job description text")
    top_k: Optional[int] = Field(default=10, ge=1, le=50, description="Number of top candidates")


class ScoreBreakdown(BaseModel):
    semantic: float
    skills: float
    experience: float
    behavior: float
    career: float


class CandidateResult(BaseModel):
    rank: int
    candidate_id: str
    final_score: float
    scores: ScoreBreakdown
    reasoning: list[str]


class RankResponse(BaseModel):
    jd_snippet: str
    total_evaluated: int
    results: list[CandidateResult]
    pipeline_info: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    candidates_loaded: int


class CandidateSummary(BaseModel):
    candidate_id: str
    headline: str
    current_role: str
    location: str
    experience_years: float
    skills: list[str]
    open_to_work: bool


# ─── Helper ───────────────────────────────────────────────────────────────────

def _parse_profile(profile_text: str) -> dict:
    """Extract structured fields from a profile_text string."""
    lines = profile_text.splitlines()
    data: dict = {"skills": [], "open_to_work": False, "headline": "", "current_role": "", "location": "", "experience_years": 0.0}

    for line in lines:
        line = line.strip()
        if line.startswith("Headline:"):
            data["headline"] = line.replace("Headline:", "").strip()
        elif line.startswith("Current Role:"):
            data["current_role"] = line.replace("Current Role:", "").strip()
        elif line.startswith("Location:"):
            data["location"] = line.replace("Location:", "").strip()
        elif line.startswith("Experience:"):
            try:
                data["experience_years"] = float(line.replace("Experience:", "").replace("years", "").strip())
            except ValueError:
                pass
        elif line.startswith("Skills:"):
            raw = line.replace("Skills:", "").strip()
            data["skills"] = [s.strip() for s in raw.split(",") if s.strip()]
        elif "Open to work: True" in line:
            data["open_to_work"] = True

    return data


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Returns API health status and number of candidates in the database."""
    try:
        candidates = load_candidates()
        count = len(candidates)
    except Exception:
        count = 0
    return HealthResponse(status="ok", version="1.0.0", candidates_loaded=count)


@app.post("/api/rank", response_model=RankResponse, tags=["Ranking"])
def rank_candidates(req: RankRequest):
    """
    Run the full AI ranking pipeline on the provided job description.
    Returns top-k ranked candidates with scores and factual reasoning.
    """
    try:
        raw_results = run_pipeline(req.jd_text, top_k=req.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(exc)}")

    results: list[CandidateResult] = []
    for rank_idx, r in enumerate(raw_results, start=1):
        reasoning_items = [item.strip() for item in r["reasoning"].split("|") if item.strip()]
        results.append(
            CandidateResult(
                rank=rank_idx,
                candidate_id=r["candidate_id"],
                final_score=round(r["final_score"], 4),
                scores=ScoreBreakdown(
                    semantic=round(r["semantic_score"], 4),
                    skills=round(r["skill_score"], 4),
                    experience=round(r["experience_score"], 4),
                    behavior=round(r["behavior_score"], 4),
                    career=round(r["career_score"], 4),
                ),
                reasoning=reasoning_items,
            )
        )

    jd_snippet = req.jd_text.strip()[:120] + ("…" if len(req.jd_text.strip()) > 120 else "")

    return RankResponse(
        jd_snippet=jd_snippet,
        total_evaluated=len(raw_results),
        results=results,
        pipeline_info={
            "retrieval": "BM25 + FAISS (RRF fusion)",
            "scoring": "Semantic 40% | Skills 25% | Experience 15% | Behavior 10% | Career 10%",
            "latency": "4-200ms",
            "cost": "$0 (no LLM)",
        },
    )


@app.get("/api/candidates", response_model=list[CandidateSummary], tags=["Candidates"])
def list_candidates():
    """Returns a summary of all candidates in the database."""
    try:
        candidates = load_candidates()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    result = []
    for c in candidates:
        parsed = _parse_profile(c["profile_text"])
        result.append(
            CandidateSummary(
                candidate_id=c["candidate_id"],
                headline=parsed["headline"],
                current_role=parsed["current_role"],
                location=parsed["location"],
                experience_years=parsed["experience_years"],
                skills=parsed["skills"][:8],
                open_to_work=parsed["open_to_work"],
            )
        )
    return result


@app.get("/api/candidates/{candidate_id}", tags=["Candidates"])
def get_candidate(candidate_id: str):
    """Returns full profile text for a specific candidate."""
    try:
        candidates = load_candidates()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    candidate_map = {c["candidate_id"]: c for c in candidates}
    if candidate_id not in candidate_map:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")

    c = candidate_map[candidate_id]
    parsed = _parse_profile(c["profile_text"])
    return {
        "candidate_id": c["candidate_id"],
        "profile_text": c["profile_text"],
        **parsed,
    }
