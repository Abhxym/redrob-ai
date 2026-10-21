import { useState } from 'react';
import { Sparkles, LoaderCircle, RotateCcw } from 'lucide-react';
import { SAMPLE_JDS } from '../lib/profile.js';

const MIN_CHARS = 20;

export default function Composer({ onSubmit, loading, compact, notReady }) {
  const [text, setText] = useState('');
  const [topK, setTopK] = useState(10);
  const ready = text.trim().length >= MIN_CHARS && !loading && !notReady;

  const submit = e => {
    e?.preventDefault();
    if (ready) onSubmit(text.trim(), topK);
  };

  return (
    <form className={`composer card ${compact ? 'composer-compact' : ''}`} onSubmit={submit}>
      <div className="composer-head">
        <div>
          <h2 className="composer-title">Job description</h2>
          <p className="muted small">Paste a JD. The pipeline parses it, retrieves, fuses, scores and explains.</p>
        </div>
        <div className="samples" role="group" aria-label="Load a sample job description">
          {SAMPLE_JDS.map(s => (
            <button key={s.label} type="button" className="pill" onClick={() => setText(s.text)}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <textarea
        className="composer-input"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submit(e); }}
        placeholder="e.g. Senior ML Engineer, 5+ years, Python, PyTorch, vector search, MLOps on AWS…"
        rows={compact ? 4 : 9}
        aria-label="Job description"
      />

      <div className="composer-foot">
        <div className="composer-meta">
          <label className="topk">
            <span className="muted small">Shortlist size</span>
            <input
              type="range"
              min={5}
              max={100}
              step={5}
              value={topK}
              onChange={e => setTopK(Number(e.target.value))}
            />
            <span className="mono topk-val">{topK}</span>
          </label>
          <span className="muted small mono">{text.trim().length} chars</span>
          {text && (
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setText('')}>
              <RotateCcw size={13} /> Clear
            </button>
          )}
        </div>
        <button type="submit" className="btn btn-primary" disabled={!ready} title={notReady ? 'Models are still loading' : undefined}>
          {loading || notReady ? <LoaderCircle size={16} className="spin" /> : <Sparkles size={16} />}
          {loading ? 'Ranking…' : notReady ? 'Loading models…' : 'Rank candidates'}
          {!loading && !notReady && <kbd>Ctrl ↵</kbd>}
        </button>
      </div>
    </form>
  );
}
