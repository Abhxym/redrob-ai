import { useState } from 'react';
import { Search, Loader, FileText, ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import './JDInput.css';

const SAMPLE_JD = `Senior Machine Learning Engineer — Search & Ranking

We're looking for an experienced ML engineer to build and scale our search ranking systems.

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

This is a senior IC role working on high-impact ML systems.`;

const TOP_K_OPTIONS = [5, 10, 15, 20, 30];

export default function JDInput({ onSubmit, isLoading }) {
  const [jdText, setJdText] = useState('');
  const [topK, setTopK] = useState(10);
  const [showSample, setShowSample] = useState(false);

  const charCount = jdText.trim().length;
  const isValid = charCount >= 20;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid || isLoading) return;
    onSubmit(jdText, topK);
  };

  const handleLoadSample = () => {
    setJdText(SAMPLE_JD);
    setShowSample(false);
  };

  return (
    <section className="jd-section fade-up">
      <div className="jd-header">
        <div>
          <h1 className="jd-title">
            Find the <span className="gradient-text">perfect candidate</span>
          </h1>
          <p className="jd-subtitle">
            Paste your job description — our AI pipeline ranks candidates using hybrid BM25+FAISS retrieval with multi-signal scoring.
          </p>
        </div>
        <div className="jd-pipeline-badges">
          <span className="badge badge-cyan">BM25</span>
          <span className="pipeline-plus">+</span>
          <span className="badge badge-violet">FAISS</span>
          <span className="pipeline-plus">→</span>
          <span className="badge badge-emerald">RRF Fusion</span>
          <span className="pipeline-plus">→</span>
          <span className="badge badge-amber">5-Signal Ranking</span>
        </div>
      </div>

      <form className="jd-form card card-glass" onSubmit={handleSubmit}>
        {/* Textarea */}
        <div className="jd-textarea-wrap">
          <div className="jd-textarea-label">
            <FileText size={14} />
            <span>Job Description</span>
            <span className="jd-char-count">{charCount} chars</span>
          </div>
          <textarea
            id="jd-textarea"
            className="jd-textarea"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the full job description here…&#10;&#10;Include: role title, required skills, experience level, and responsibilities."
            rows={12}
            disabled={isLoading}
            autoFocus
          />
          {!jdText && (
            <button
              type="button"
              className="sample-btn"
              onClick={handleLoadSample}
            >
              <Sparkles size={13} />
              Load sample JD
            </button>
          )}
        </div>

        {/* Controls row */}
        <div className="jd-controls">
          {/* Top K selector */}
          <div className="topk-wrap">
            <label htmlFor="topk-select" className="topk-label">Top candidates</label>
            <select
              id="topk-select"
              className="topk-select"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              disabled={isLoading}
            >
              {TOP_K_OPTIONS.map((k) => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </div>

          {/* Submit */}
          <button
            type="submit"
            id="rank-btn"
            className={`btn btn-primary btn-lg ${(!isValid || isLoading) ? 'btn-disabled' : ''}`}
            disabled={!isValid || isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner" />
                Ranking…
              </>
            ) : (
              <>
                <Search size={18} />
                Rank Candidates
              </>
            )}
          </button>
        </div>

        {!isValid && charCount > 0 && (
          <p className="jd-validation">⚠ Please enter at least 20 characters.</p>
        )}
      </form>

      {/* How it works accordion */}
      <button
        type="button"
        className="how-it-works-toggle"
        onClick={() => setShowSample(s => !s)}
        aria-expanded={showSample}
      >
        How does the AI pipeline work?
        {showSample ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {showSample && (
        <div className="pipeline-steps fade-in card">
          {[
            { step: '01', label: 'JD Parsing', desc: 'Extracts skills (77-skill DB), experience, domain, leadership signals — <1ms', color: 'var(--cyan)' },
            { step: '02', label: 'BM25 Search', desc: 'Keyword-based retrieval catches exact tech terms: Python, FAISS, PyTorch — 1ms', color: 'var(--violet)' },
            { step: '03', label: 'FAISS Search', desc: 'Semantic search (384-dim vectors) finds conceptually similar candidates — 1-2ms', color: '#818cf8' },
            { step: '04', label: 'RRF Fusion', desc: 'Reciprocal Rank Fusion combines both sources, preventing rank dominance — sub-ms', color: 'var(--emerald)' },
            { step: '05', label: 'Multi-Signal Scoring', desc: 'Weighted formula: Semantic 40% | Skills 25% | Experience 15% | Behavior 10% | Career 10%', color: 'var(--amber)' },
            { step: '06', label: 'Reasoning', desc: 'Factual explanations extracted from skill matches, experience level, and engagement signals', color: 'var(--rose)' },
          ].map((item, i) => (
            <div key={i} className="pipeline-step" style={{ '--step-color': item.color }}>
              <div className="step-num">{item.step}</div>
              <div>
                <div className="step-label">{item.label}</div>
                <div className="step-desc">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
