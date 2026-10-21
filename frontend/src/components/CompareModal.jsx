import { useEffect } from 'react';
import { X } from 'lucide-react';
import { SIGNALS, pct } from '../lib/profile.js';

export default function CompareModal({ results, onClose, onRemove }) {
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const signals = SIGNALS.filter(s => results.some(r => r.scores[s.key] != null));
  const best = key => Math.max(...results.map(r => (key === 'final' ? r.final_score : r.scores[key] ?? 0)));
  const cell = (r, key, v) => (
    <td key={r.candidate_id} className={`num mono ${v === best(key) ? 'is-best' : ''}`}>{pct(v)}</td>
  );

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label="Compare candidates">
      <div className="scrim" onClick={onClose} />
      <div className="modal">
        <div className="modal-head">
          <h2>Compare candidates</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><X size={15} /></button>
        </div>
        <div className="modal-body">
          <table className="compare">
            <thead>
              <tr>
                <th />
                {results.map(r => (
                  <th key={r.candidate_id}>
                    <div className="strong">#{r.rank} {r.current_title}</div>
                    <div className="sub mono">{r.candidate_id}</div>
                    <button type="button" className="link" onClick={() => onRemove(r.candidate_id)}>Remove</button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="strong"><th>Final score</th>{results.map(r => cell(r, 'final', r.final_score))}</tr>
              {signals.map(s => (
                <tr key={s.key}>
                  <th><span className="swatch" style={{ background: s.color }} />{s.label}</th>
                  {results.map(r => cell(r, s.key, r.scores[s.key] ?? 0))}
                </tr>
              ))}
              <tr><th>Experience</th>{results.map(r => <td key={r.candidate_id} className="num mono">{r.experience_years} yrs</td>)}</tr>
              <tr><th>Location</th>{results.map(r => <td key={r.candidate_id}>{r.location || '—'}</td>)}</tr>
              <tr><th>Notice period</th>{results.map(r => <td key={r.candidate_id}>{r.notice_days != null ? `${r.notice_days} days` : '—'}</td>)}</tr>
              <tr><th>Matched skills</th>{results.map(r => <td key={r.candidate_id} className="wrap">{r.matched_skills.join(', ') || '—'}</td>)}</tr>
            </tbody>
          </table>
          <p className="hint">Highest value in each row is highlighted.</p>
        </div>
      </div>
    </div>
  );
}
