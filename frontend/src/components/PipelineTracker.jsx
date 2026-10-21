import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';

const STEPS = [
  { name: 'Parse JD', detail: 'Skills, seniority, JD type' },
  { name: 'BM25', detail: 'Keyword recall, top 75' },
  { name: 'FAISS', detail: 'Semantic recall, top 75' },
  { name: 'RRF fusion', detail: '1 / (60 + rank) → top 100' },
  { name: 'Multi-signal score', detail: 'Dynamic, JD-aware weights' },
  { name: 'Cross-encoder', detail: 'Re-rank JD × profile pairs' },
  { name: 'Explain', detail: 'Factual reasons' },
];

// Rough share of a warm request spent before each step starts (retrieval dominates).
const PACE_MS = [0, 300, 7000, 10500, 11000, 11500, 14200];

// The API runs the pipeline in one request, so progress while loading is paced client-side;
// it never shows the final step complete until the response arrives.
export default function PipelineTracker({ loading, done, info }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!loading) return;
    setStep(0);
    const t0 = Date.now();
    const id = setInterval(() => {
      const elapsed = Date.now() - t0;
      const next = PACE_MS.findLastIndex(ms => elapsed >= ms);
      setStep(Math.min(next, STEPS.length - 1));
    }, 250);
    return () => clearInterval(id);
  }, [loading]);

  const active = done ? STEPS.length : step;
  const t = info?.timings;

  return (
    <section className="pipeline card" aria-label="Ranking pipeline">
      <div className="pipeline-head">
        <span className="eyebrow">Pipeline</span>
        {done && info?.latency && <span className="mono small muted">{info.latency} end-to-end</span>}
        {loading && <span className="mono small muted">running…</span>}
      </div>
      <ol className="pipeline-steps">
        {STEPS.map((s, i) => {
          const state = i < active ? 'done' : i === active && loading ? 'active' : 'idle';
          let detail = s.detail;
          if (done && t) {
            if (s.name === 'FAISS') detail = `${(info.corpus_size ?? 0).toLocaleString()} profiles searched`;
            if (s.name === 'RRF fusion') detail = `Retrieval ${(t.retrieval_ms / 1000).toFixed(1)}s total`;
            if (s.name === 'Cross-encoder') detail = info.reranker ? `${(t.rerank_ms / 1000).toFixed(1)}s · 70/30 blend` : 'Skipped';
            if (s.name === 'Multi-signal score' && info.jd_type) detail = `Weights for ${info.jd_type.replace('_', ' ')} JD`;
          }
          return (
            <li key={s.name} className={`pstep pstep-${state}`}>
              <span className="pstep-dot">{state === 'done' ? <Check size={12} strokeWidth={3} /> : i + 1}</span>
              <span className="pstep-text">
                <span className="pstep-name">{s.name}</span>
                <span className="pstep-detail">{detail}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
