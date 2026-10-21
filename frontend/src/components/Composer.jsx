import { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { SAMPLE_JDS } from '../lib/profile.js';

const MIN_CHARS = 20;

export default function Composer({ onSubmit, loading, notReady, compact, initialText = '', initialTopK = 10 }) {
  const [text, setText] = useState(initialText);
  const [topK, setTopK] = useState(initialTopK);
  const ready = text.trim().length >= MIN_CHARS && !loading && !notReady;

  const submit = e => {
    e?.preventDefault();
    if (ready) onSubmit(text.trim(), topK);
  };

  return (
    <form className={`composer ${compact ? 'composer-compact' : ''}`} onSubmit={submit}>
      <textarea
        className="composer-input"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submit(e); }}
        placeholder="Paste a job description…"
        rows={compact ? 8 : 6}
        aria-label="Job description"
      />
      <div className="pill-pair">
        <button type="submit" className="pill pill-dark" disabled={!ready}>
          {loading ? 'Ranking…' : notReady ? 'Loading models…' : 'Rank candidates'}
          <ArrowRight size={16} />
        </button>
        <span className="pill-bridge" aria-hidden="true" />
        <label className="pill pill-light">
          <select
            value=""
            onChange={e => { const s = SAMPLE_JDS[Number(e.target.value)]; if (s) setText(s.text); }}
            aria-label="Load an example job description"
          >
            <option value="" disabled>Try an example</option>
            {SAMPLE_JDS.map((s, i) => <option key={s.label} value={i}>{s.label}</option>)}
          </select>
          <span className="pill-dot" aria-hidden="true">▾</span>
        </label>
      </div>
      <label className="topk">
        Top
        <input
          type="number"
          min={1}
          max={100}
          value={topK}
          onChange={e => setTopK(Math.max(1, Math.min(100, Number(e.target.value) || 1)))}
        />
        candidates · Ctrl + Enter
      </label>
    </form>
  );
}
