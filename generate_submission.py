"""
generate_submission.py

Full pipeline: JD -> BM25 + FAISS (real sentence embeddings) -> Feature Scoring -> Top 100
Outputs: outputs/submission.csv  (exact challenge format)
         outputs/submission.xlsx (rich 17-column view)
"""
import json, pickle, math, csv, os, time, zipfile
import numpy as np
from collections import defaultdict
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
JSONL_PATH  = r"[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl"
CACHE_DIR   = Path("data/submission_cache")
BM25_CACHE  = CACHE_DIR / "bm25_full.pkl"
FAISS_CACHE = CACHE_DIR / "faiss_full.bin"
IDS_CACHE   = CACHE_DIR / "candidate_ids.pkl"
OUT_CSV     = "outputs/submission.csv"
OUT_XLSX    = "outputs/submission.xlsx"
EMBED_MODEL = "all-MiniLM-L6-v2"

# ── Skill ontology: JD skill -> candidate skill aliases ───────────────────
SKILL_ALIASES = {
    "Python":                   ["python"],
    "PyTorch":                  ["pytorch", "deep learning", "neural network", "torch"],
    "TensorFlow":               ["tensorflow", "keras", "deep learning", "tf"],
    "Machine Learning":         ["machine learning", "ml", "xgboost", "lightgbm", "sklearn", "scikit-learn", "catboost", "gradient boosting"],
    "NLP":                      ["nlp", "natural language processing", "text classification", "bert", "transformers", "text mining", "named entity", "sentiment"],
    "FAISS":                    ["faiss", "vector search", "vector database", "pinecone", "weaviate", "milvus", "qdrant", "chroma", "ann", "approximate nearest"],
    "Elasticsearch":            ["elasticsearch", "opensearch", "solr", "search infrastructure", "indexing"],
    "Embeddings":               ["embeddings", "sentence transformers", "word2vec", "fasttext", "dense retrieval", "bi-encoder"],
    "LLM":                      ["llm", "large language model", "gpt", "langchain", "fine-tuning llms", "prompt engineering", "rag", "retrieval augmented", "llama", "mistral"],
    "Recommendation Systems":   ["recommendation systems", "collaborative filtering", "ranking", "personalization", "recsys"],
    "Information Retrieval":    ["information retrieval", "bm25", "ranking", "search", "ir", "learning to rank", "ltr"],
    "MLOps":                    ["mlops", "mlflow", "kubeflow", "weights & biases", "bentoml", "airflow", "model serving", "model deployment", "feature store"],
    "Data Pipeline":            ["data pipeline", "spark", "kafka", "airflow", "etl", "pyspark", "flink", "dbt", "data engineering"],
    "AWS":                      ["aws", "gcp", "azure", "cloud", "sagemaker", "vertex ai", "ec2", "s3", "lambda"],
    "Go":                       ["go", "golang"],
    "Docker":                   ["docker", "kubernetes", "k8s", "containerization", "helm"],
    "SQL":                      ["sql", "postgresql", "mysql", "bigquery", "snowflake", "redshift", "database"],
    "Spark":                    ["spark", "pyspark", "apache spark", "databricks"],
    "Distributed Systems":      ["distributed systems", "microservices", "kafka", "grpc", "system design"],
    "Computer Vision":          ["computer vision", "opencv", "image classification", "object detection", "cnn", "yolo"],
}

# ── Profile text for BM25 (keyword-rich) ──────────────────────────────────
def build_profile_text(c):
    p      = c["profile"]
    skills = " ".join(s["name"] for s in c.get("skills", []))
    titles = " ".join(h.get("title", "") + " " + h.get("company", "") for h in c.get("career_history", []))
    descs  = " ".join(h.get("description", "") for h in c.get("career_history", []))
    s      = c.get("redrob_signals", {})
    return (
        f"{p.get('current_title','')} with {p.get('years_of_experience',0)} years of experience. "
        f"Skills: {skills}. Career: {titles}. {descs[:300]} "
        f"Open to work: {s.get('open_to_work_flag', False)} | "
        f"Notice: {s.get('notice_period_days', 90)} days | "
        f"GitHub activity: {s.get('github_activity_score', -1)} | "
        f"Recruiter response rate: {s.get('recruiter_response_rate', 0.5)*100:.0f}% | "
        f"Interview completion: {s.get('interview_completion_rate', 0.5)*100:.0f}%"
    )

# ── BM25 ───────────────────────────────────────────────────────────────────
class SimpleBM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / self.corpus_size
        self.idf = {}
        for doc in corpus:
            for w in set(doc):
                self.idf[w] = self.idf.get(w, 0) + 1
        for w in self.idf:
            self.idf[w] = math.log((self.corpus_size - self.idf[w] + 0.5) / (self.idf[w] + 0.5))
        self.corpus = corpus

    def get_scores(self, query):
        scores = [0.0] * self.corpus_size
        for q in query:
            if q not in self.idf:
                continue
            idf = self.idf[q]
            for i, doc in enumerate(self.corpus):
                f = doc.count(q)
                if f == 0:
                    continue
                norm = 1 - self.b + self.b * len(doc) / self.avgdl
                scores[i] += idf * f * (self.k1 + 1) / (f + self.k1 * norm)
        return scores

# ── Load candidates ────────────────────────────────────────────────────────
def load_candidates():
    print("Loading candidates.jsonl ...")
    t = time.time()
    candidates = [json.loads(l) for l in open(JSONL_PATH, encoding="utf-8") if l.strip()]
    print(f"  Loaded {len(candidates):,} candidates in {time.time()-t:.1f}s")
    return candidates

# The cached index may have been pickled with this file running as __main__;
# resolve SimpleBM25 here so it also loads when imported (e.g. by the API).
class _BM25Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == "SimpleBM25":
            return SimpleBM25
        return super().find_class(module, name)

# ── Build or load indexes ──────────────────────────────────────────────────
def build_or_load_indexes(candidates):
    import faiss
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if all(p.exists() for p in [BM25_CACHE, FAISS_CACHE, IDS_CACHE]):
        print("Loading cached indexes ...")
        with open(BM25_CACHE, "rb") as f:
            bm25 = _BM25Unpickler(f).load()
        faiss_index = faiss.read_index(str(FAISS_CACHE))
        with open(IDS_CACHE, "rb") as f:
            ids = pickle.load(f)
        print(f"  Indexes loaded ({len(ids):,} candidates)")
        return bm25, faiss_index, ids

    print("Building indexes (first run — ~2-3 min for embeddings) ...")
    ids   = [c["candidate_id"] for c in candidates]
    texts = [build_profile_text(c) for c in candidates]

    # BM25
    t = time.time()
    corpus = [tx.lower().split() for tx in texts]
    bm25 = SimpleBM25(corpus)
    with open(BM25_CACHE, "wb") as f:
        pickle.dump(bm25, f)
    print(f"  BM25 built in {time.time()-t:.1f}s")

    # FAISS with real sentence embeddings
    t = time.time()
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBED_MODEL)
    print(f"  Encoding {len(texts):,} candidates with {EMBED_MODEL} ...")
    embs = model.encode(texts, batch_size=512, show_progress_bar=True,
                        normalize_embeddings=True).astype("float32")
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)
    faiss.write_index(index, str(FAISS_CACHE))
    with open(IDS_CACHE, "wb") as f:
        pickle.dump(ids, f)
    print(f"  FAISS built in {time.time()-t:.1f}s")

    return bm25, index, ids

# ── Hybrid retrieval ───────────────────────────────────────────────────────
_MODEL = None
def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer(EMBED_MODEL)
    return _MODEL

def hybrid_search(query, bm25, faiss_index, ids, top_n=75):
    import faiss as faiss_lib
    # FAISS semantic search
    q_emb = _get_model().encode([query], normalize_embeddings=True).astype("float32")
    _, fi  = faiss_index.search(q_emb, top_n)
    faiss_hits = {ids[i]: r+1 for r, i in enumerate(fi[0]) if i >= 0}

    # BM25 keyword search
    scores  = bm25.get_scores(query.lower().split())
    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_n]
    bm25_hits = {ids[i]: r+1 for r, i in enumerate(top_idx)}

    # RRF fusion
    rrf = defaultdict(float)
    for cid, rank in faiss_hits.items():
        rrf[cid] += 1.0 / (60 + rank)
    for cid, rank in bm25_hits.items():
        rrf[cid] += 1.0 / (60 + rank)

    return {cid: sc for cid, sc in sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:100]}

# ── Accurate experience from career_history (no double-counting overlaps) ─
def calc_experience_years(c):
    from datetime import date
    intervals = []
    for h in c.get("career_history", []):
        try:
            start = date.fromisoformat(h["start_date"])
            end   = date.fromisoformat(h["end_date"]) if h.get("end_date") else date.today()
            intervals.append((start, end))
        except Exception:
            # fallback: use duration_months directly if dates are bad
            intervals = None
            break

    if intervals:
        # merge overlapping intervals to avoid double-counting
        intervals.sort()
        merged, total_days = [], 0
        for start, end in intervals:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append([start, end])
        total_days = sum((e - s).days for s, e in merged)
        return round(total_days / 365.25, 1)

    # fallback
    months = sum(h.get("duration_months", 0) for h in c.get("career_history", []))
    return round(months / 12, 1)

# ── Skill score with ontology + proficiency + endorsements ────────────────
PROFICIENCY_WEIGHT = {"beginner": 0.5, "intermediate": 0.75, "advanced": 1.0, "expert": 1.0}

def calc_skill_score(c, jd_skills):
    if not jd_skills:
        return 1.0, []
    cand_skills = {s["name"].lower(): s for s in c.get("skills", [])}
    matched, matched_names = 0.0, []
    for jd_skill in jd_skills:
        aliases = SKILL_ALIASES.get(jd_skill, [jd_skill.lower()])
        best = 0.0
        best_name = None
        for alias in aliases:
            for cname, cskill in cand_skills.items():
                if alias in cname or cname in alias:
                    prof  = PROFICIENCY_WEIGHT.get(cskill.get("proficiency", "intermediate"), 0.75)
                    endr  = min(cskill.get("endorsements", 0) / 20, 1.0)  # cap at 20 endorsements
                    score = 0.6 * prof + 0.4 * endr
                    if score > best:
                        best = score
                        best_name = cskill["name"]
        matched += best
        if best_name:
            matched_names.append((best_name, round(best, 2)))
    return round(min(matched / len(jd_skills), 1.0), 4), matched_names

# ── Experience score from actual career history ────────────────────────────
def calc_experience_score(c, required_years):
    if required_years == 0:
        return 1.0
    actual = calc_experience_years(c)
    return round(min(actual / required_years, 1.0), 4)

# ── Career score from title progression ───────────────────────────────────
LEVEL_MAP = {"intern":0,"junior":1,"associate":1,"analyst":2,"engineer":2,
             "senior":3,"staff":4,"lead":4,"principal":5,"manager":4,
             "director":6,"vp":7,"head":6}

def calc_career_score(c):
    history = c.get("career_history", [])
    levels  = []
    for h in history:
        t = h.get("title", "").lower()
        for kw, lv in LEVEL_MAP.items():
            if kw in t:
                levels.append(lv)
                break
    if not levels:
        return 0.4
    highest    = max(levels)
    base       = highest / 7.0
    progression = 0.15 if len(set(levels)) >= 2 else 0.0
    tenure_bonus = 0.1 if len(history) >= 3 else 0.0
    return round(min(base + progression + tenure_bonus, 1.0), 4)

# ── Behavior score with offer_acceptance_rate + skill assessments ──────────
def calc_behavior_score(c):
    s   = c.get("redrob_signals", {})
    rr  = s.get("recruiter_response_rate", 0.5)
    cr  = s.get("interview_completion_rate", 0.5)
    gh  = s.get("github_activity_score", -1)
    gs  = (gh / 100) if gh >= 0 else 0.3
    sv  = min(s.get("saved_by_recruiters_30d", 0) / 20, 1.0)
    oa  = s.get("offer_acceptance_rate", -1)
    oas = oa if oa >= 0 else 0.5
    # avg skill assessment score if available
    assessments = s.get("skill_assessment_scores", {})
    sa = (sum(assessments.values()) / len(assessments) / 100) if assessments else 0.5
    return round(0.25*rr + 0.25*cr + 0.15*gs + 0.10*sv + 0.15*oas + 0.10*sa, 4)

# ── Final weighted score (dynamic JD-aware weights) ──────────────────────
def score_candidate(c, rrf_score, jd_req, weights, max_rrf):
    sk, matched_names = calc_skill_score(c, jd_req["skills"])
    ex = calc_experience_score(c, jd_req["experience"])
    ca = calc_career_score(c)
    bh = calc_behavior_score(c)
    sem = round(rrf_score / max_rrf if max_rrf > 0 else 0.0, 4)
    final = round(
        weights["semantic_score"]    * sem +
        weights["skill_score"]       * sk  +
        weights["experience_score"]  * ex  +
        weights["behavior_score"]    * bh  +
        weights["career_score"]      * ca,
        4
    )
    return final, sk, ex, bh, ca, sem, matched_names

# ── Rich reasoning ─────────────────────────────────────────────────────────
def build_reasoning(c, jd_req, matched_names, sk, ex, bh, ca):
    parts = []
    s     = c.get("redrob_signals", {})
    p     = c["profile"]

    # Skills with endorsement context
    if len(matched_names) >= 4:
        top = ", ".join(n for n, _ in matched_names[:4])
        parts.append(f"Strong match on {top}")
    elif len(matched_names) >= 2:
        top = ", ".join(n for n, _ in matched_names[:3])
        parts.append(f"Relevant skills: {top}")
    elif matched_names:
        parts.append(f"Has {matched_names[0][0]} experience")

    # Accurate experience
    actual_yrs = calc_experience_years(c)
    req        = jd_req["experience"]
    parts.append(f"{actual_yrs:.1f} yrs exp ({'meets' if actual_yrs >= req else 'below'} {req}+ req)")

    # Most recent company + title
    history = c.get("career_history", [])
    current = next((h for h in history if h.get("is_current")), None)
    if current:
        parts.append(f"Currently {current['title']} at {current['company']}")

    # Career progression
    titles = [h.get("title","") for h in history]
    if len(titles) >= 2:
        parts.append(f"Progressed: {' -> '.join(t.split()[0] for t in titles[-2:])}")

    # Skill assessments
    assessments = s.get("skill_assessment_scores", {})
    if assessments:
        best_k = max(assessments, key=assessments.get)
        parts.append(f"Assessment: {best_k} {assessments[best_k]:.0f}/100")

    # Behavioral signals
    rr = s.get("recruiter_response_rate", 0)
    if rr >= 0.7:
        parts.append(f"Response rate {rr:.0%}")
    oa = s.get("offer_acceptance_rate", -1)
    if oa >= 0.7:
        parts.append(f"Offer acceptance {oa:.0%}")
    gh = s.get("github_activity_score", -1)
    if gh >= 50:
        parts.append(f"GitHub {gh:.0f}/100")

    # Availability
    if s.get("open_to_work_flag"):
        parts.append("Open to work")
    np_ = s.get("notice_period_days", 90)
    if np_ <= 30:
        parts.append(f"{np_}-day notice")

    return " | ".join(parts)

# ── XLSX writer ────────────────────────────────────────────────────────────
XLSX_HEADERS = [
    "Rank","Candidate ID","Final Score","Current Title","Location","Years Exp",
    "Skill Score","Exp Score","Behavior Score","Career Score","Semantic Score",
    "Matched Skills","Open to Work","Notice (Days)","Response Rate",
    "GitHub Score","Offer Acceptance","Reasoning"
]
XLSX_COLS = [
    "rank","candidate_id","score","current_title","location","years_exp",
    "skill_score","exp_score","behavior_score","career_score","semantic_score",
    "matched_skills","open_to_work","notice_days","response_rate",
    "github_score","offer_acceptance","reasoning"
]
XLSX_WIDTHS = [6,16,10,26,16,8,8,8,8,8,8,38,10,10,10,10,12,60]

def _esc(v):
    return str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

SCORE_COLS = {"score", "skill_score", "exp_score", "behavior_score", "career_score", "semantic_score", "response_rate", "offer_acceptance"}

def _cell(col, row, val, style=""):
    col_letter = chr(ord("A")+col) if col < 26 else chr(ord("A")+(col//26)-1)+chr(ord("A")+(col%26))
    ref = f"{col_letter}{row}"
    s = f' s="{style}"' if style else ""
    if isinstance(val, (int, float)):
        return f'<c r="{ref}" t="n"{s}><v>{val}</v></c>'
    return f'<c r="{ref}" t="inlineStr"{s}><is><t>{_esc(str(val))}</t></is></c>'

def write_xlsx(rows, path):
    col_defs = "".join(
        f'<col min="{j+1}" max="{j+1}" width="{XLSX_WIDTHS[j]}" customWidth="1"/>'
        for j in range(len(XLSX_COLS))
    )
    last_col = chr(ord("A") + len(XLSX_COLS) - 1)
    sheet_rows = []
    hcells = "".join(_cell(j, 1, XLSX_HEADERS[j], "1") for j in range(len(XLSX_HEADERS)))
    sheet_rows.append(f'<row r="1">{hcells}</row>')
    for i, row in enumerate(rows, 2):
        cells = "".join(
            _cell(j, i, row[XLSX_COLS[j]], "2" if XLSX_COLS[j] in SCORE_COLS else "")
            for j in range(len(XLSX_COLS))
        )
        sheet_rows.append(f'<row r="{i}">{cells}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        f'<cols>{col_defs}</cols>'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        f'<autoFilter ref="A1:{last_col}1"/>'
        '</worksheet>'
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="0.00"/></numFmts>'
        '<fonts><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills>'
        '<fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF4472C4"/></patternFill></fill>'
        '</fills>'
        '<borders><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs>'
        '<xf numFmtId="0"   fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0"   fontId="1" fillId="2" borderId="0" xfId="0"><alignment horizontal="center" wrapText="1"/></xf>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '</cellXfs></styleSheet>'
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>')
        zf.writestr("_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>')
        zf.writestr("xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Top 100 Candidates" sheetId="1" r:id="rId1"/></sheets>'
            '</workbook>')
        zf.writestr("xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '</Relationships>')
        zf.writestr("xl/styles.xml", styles_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    print(f"XLSX saved:  {path}")

# ── Main pipeline ──────────────────────────────────────────────────────────
# ── Cached state (lets the API reuse data, indexes and models across requests) ─
_STATE = None
_CE_MODEL = None
CE_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

def load_state():
    """Load candidates + BM25/FAISS indexes once per process."""
    global _STATE
    if _STATE is None:
        candidates = load_candidates()
        bm25, faiss_index, ids = build_or_load_indexes(candidates)
        _STATE = {
            "cand_map": {c["candidate_id"]: c for c in candidates},
            "bm25": bm25, "faiss_index": faiss_index, "ids": ids,
        }
    return _STATE

def _get_ce_model():
    global _CE_MODEL
    if _CE_MODEL is None:
        from sentence_transformers import CrossEncoder
        _CE_MODEL = CrossEncoder(CE_MODEL_NAME)
    return _CE_MODEL


def rank(jd_text):
    """
    JD -> hybrid retrieval -> feature scoring -> cross-encoder rerank.
    Returns (rows sorted by final score, meta dict with weights/timings).
    """
    from preprocessing.jd_parser import JDParser
    timings = {}
    t0 = time.time()

    # 1. Parse JD
    jd_req = JDParser().parse(jd_text)
    print(f"JD: {len(jd_req['skills'])} skills, {jd_req['experience']} yrs req, domain={jd_req['domain']}")
    print(f"Skills: {', '.join(jd_req['skills'])}\n")

    # 2. Load data + indexes
    state       = load_state()
    cand_map    = state["cand_map"]
    bm25, faiss_index, ids = state["bm25"], state["faiss_index"], state["ids"]

    # 3. Hybrid retrieval
    print("\nRunning hybrid retrieval ...")
    t = time.time()
    top100_rrf = hybrid_search(jd_text, bm25, faiss_index, ids)
    timings["retrieval_ms"] = round((time.time() - t) * 1000, 1)
    print(f"  Retrieved {len(top100_rrf)} candidates in {timings['retrieval_ms']:.0f}ms")

    # 4. Dynamic weights
    from ranking.dynamic_weights import DynamicWeightAdjuster
    weights  = DynamicWeightAdjuster().get_weights(jd_req, jd_text)
    jd_type  = DynamicWeightAdjuster()._classify_jd_type(jd_req, jd_text)
    max_rrf  = max(top100_rrf.values()) if top100_rrf else 1.0
    print(f"JD type: {jd_type} | Weights: sem={weights['semantic_score']:.2f} sk={weights['skill_score']:.2f} ex={weights['experience_score']:.2f} bh={weights['behavior_score']:.2f} ca={weights['career_score']:.2f}")

    # 5. Score + rank
    print("Scoring candidates ...")
    rows = []
    for cid, rrf_score in top100_rrf.items():
        c = cand_map[cid]
        fs, sk, ex, bh, ca, sem, matched_names = score_candidate(c, rrf_score, jd_req, weights, max_rrf)
        p  = c["profile"]
        s  = c.get("redrob_signals", {})
        rows.append({
            "candidate_id":   cid,
            "score":          fs,
            "rank":           0,
            "reasoning":      build_reasoning(c, jd_req, matched_names, sk, ex, bh, ca),
            # score breakdown
            "skill_score":    sk,
            "exp_score":      ex,
            "behavior_score": bh,
            "career_score":   ca,
            "semantic_score": sem,
            # display fields
            "current_title":  p.get("current_title", ""),
            "location":       p.get("location", ""),
            "years_exp":      calc_experience_years(c),
            "matched_skills": ", ".join(n for n, _ in matched_names),
            "open_to_work":   "Yes" if s.get("open_to_work_flag") else "No",
            "notice_days":    s.get("notice_period_days", 90),
            "response_rate":  round(s.get("recruiter_response_rate", 0), 2),
            "github_score":   s.get("github_activity_score", -1),
            "offer_acceptance": round(s.get("offer_acceptance_rate", -1), 2),
        })

    rows.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    # 6. Cross-encoder rerank
    print("Cross-encoder reranking ...")
    t = time.time()
    ce_applied = False
    try:
        ce_model = _get_ce_model()
        # Build (jd, candidate_summary) pairs
        pairs = []
        for r in rows:
            c  = cand_map[r["candidate_id"]]
            pt = build_profile_text(c)
            pairs.append([jd_text[:512], pt[:512]])
        ce_scores = ce_model.predict(pairs)
        # Normalise CE scores to [0,1] — ms-marco outputs roughly [-10, 10]
        ce_min, ce_max = ce_scores.min(), ce_scores.max()
        ce_range = ce_max - ce_min if ce_max > ce_min else 1.0
        for i, r in enumerate(rows):
            ce_norm = float((ce_scores[i] - ce_min) / ce_range)
            r["feature_score"] = r["score"]
            r["ce_score"] = round(ce_norm, 4)
            r["score"] = round(0.70 * r["score"] + 0.30 * ce_norm, 4)
        # Re-sort and re-rank
        rows.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        ce_applied = True
        print(f"  Cross-encoder reranking done")
    except Exception as e:
        print(f"  Cross-encoder skipped: {e}")
    timings["rerank_ms"] = round((time.time() - t) * 1000, 1)
    timings["total_ms"] = round((time.time() - t0) * 1000, 1)

    meta = {
        "jd_requirements": jd_req,
        "jd_type": jd_type,
        "weights": weights,
        "ce_applied": ce_applied,
        "ce_blend": {"feature": 0.70, "cross_encoder": 0.30},
        "retrieved": len(top100_rrf),
        "corpus_size": len(ids),
        "timings": timings,
    }
    return rows, meta


def run(jd_text, out_csv=OUT_CSV, out_xlsx=OUT_XLSX):
    print("\n=== RedRob Submission Generator ===\n")
    rows, _ = rank(jd_text)

    # 7. CSV (exact submission format)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id","rank","score","reasoning"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV saved:   {out_csv}")

    # 8. XLSX
    write_xlsx(rows, out_xlsx)

    # 7. Print top 10
    print(f"\nTop 10:")
    print(f"{'Rank':<5} {'Candidate':<15} {'Score':<7} {'Title':<32} Reasoning")
    print("-" * 110)
    for r in rows[:10]:
        print(f"{r['rank']:<5} {r['candidate_id']:<15} {r['score']:<7.4f} {r['current_title'][:30]:<32} {r['reasoning'][:55]}")

    return rows


# ── JD ─────────────────────────────────────────────────────────────────────
JD = """
Senior Machine Learning Engineer - Search & Ranking

Requirements:
- 5+ years of experience in machine learning and software engineering
- Strong proficiency in Python, PyTorch, and TensorFlow
- Experience with search systems: FAISS, Elasticsearch, or similar vector databases
- Hands-on experience with ranking algorithms and recommendation systems
- Knowledge of NLP, embeddings, and information retrieval
- Experience with MLOps tools and deployment pipelines

Nice to have:
- Experience with LLMs and fine-tuning
- Knowledge of distributed systems
- Contributions to open-source ML projects
"""

if __name__ == "__main__":
    run(JD)
