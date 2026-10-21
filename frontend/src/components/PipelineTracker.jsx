import { useEffect, useState } from 'react';

const STEPS = [
  'Parse job description',
  'BM25 keyword search',
  'FAISS semantic search',
  'Reciprocal rank fusion',
  'Feature scoring',
  'Cross-encoder rerank',
  'Write reasons',
];

// Rough share of a warm request spent before each step starts (retrieval dominates).
const PACE_MS = [0, 300, 7000, 10500, 11000, 11500, 14200];

// The API runs the whole pipeline in one request, so progress is paced client-side
// and never marks the last step done before the response arrives.
export function RunProgress() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const t0 = Date.now();
    const id = setInterval(() => setElapsed(Date.now() - t0), 200);
    return () => clearInterval(id);
  }, []);

  const step = Math.min(PACE_MS.findLastIndex(ms => elapsed >= ms), STEPS.length - 1);

  return (
    <div className="progress" aria-live="polite">
      <div className="progress-head">
        <span>Ranking</span>
        <span className="mono muted">{(elapsed / 1000).toFixed(1)} s</span>
      </div>
      <ol className="steps">
        {STEPS.map((s, i) => (
          <li key={s} className={i < step ? 'is-done' : i === step ? 'is-active' : ''}>{s}</li>
        ))}
      </ol>
    </div>
  );
}

export function RunDetails({ info }) {
  const t = info.timings || {};
  const rows = [
    ['Candidates searched', (info.corpus_size ?? 0).toLocaleString()],
    ['Retrieval (BM25 + FAISS → RRF)', `${((t.retrieval_ms ?? 0) / 1000).toFixed(1)} s`],
    ['Cross-encoder rerank', info.reranker ? `${((t.rerank_ms ?? 0) / 1000).toFixed(1)} s` : 'skipped'],
    ['Total', info.latency],
    ['JD type', info.jd_type ? info.jd_type.replace('_', ' ').replace(/^./, c => c.toUpperCase()) : '—'],
    ['Required experience', info.jd_experience != null ? `${info.jd_experience}+ yrs` : '—'],
  ];
  return (
    <table className="kv-table">
      <tbody>
        {rows.map(([k, v]) => <tr key={k}><th>{k}</th><td className="mono">{v}</td></tr>)}
      </tbody>
    </table>
  );
}
