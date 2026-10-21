import { useEffect } from 'react';
import { X } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { SIGNALS, pct } from '../lib/profile.js';

const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)'];

export default function CompareModal({ results, onClose, onRemove }) {
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const signals = SIGNALS.filter(s => results.some(r => r.scores[s.key] != null));
  const data = signals.map(s => {
    const row = { signal: s.label };
    results.forEach(r => { row[r.candidate_id] = Math.round((r.scores[s.key] ?? 0) * 100); });
    return row;
  });

  const best = key => Math.max(...results.map(r => (key === 'final' ? r.final_score : r.scores[key] ?? 0)));

  return (
    <div className="modal-wrap" role="dialog" aria-modal="true" aria-label="Compare candidates">
      <div className="drawer-scrim" onClick={onClose} />
      <div className="modal card">
        <div className="modal-head">
          <h2>Compare candidates</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><X size={16} /></button>
        </div>

        <div className="compare-grid">
          <div className="compare-chart">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={data} outerRadius="72%">
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis dataKey="signal" tick={{ fill: 'var(--text-2)', fontSize: 12 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                {results.map((r, i) => (
                  <Radar
                    key={r.candidate_id}
                    dataKey={r.candidate_id}
                    stroke={SERIES[i]}
                    fill={SERIES[i]}
                    fillOpacity={0.14}
                    strokeWidth={2}
                  />
                ))}
                <Tooltip
                  contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, color: 'var(--text)' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          <table className="compare-table">
            <thead>
              <tr>
                <th />
                {results.map((r, i) => (
                  <th key={r.candidate_id}>
                    <span className="swatch" style={{ background: SERIES[i] }} />
                    <span className="mono">#{r.rank} {r.candidate_id}</span>
                    <span className="muted small compare-sub">{r.current_title}</span>
                    <button type="button" className="link small" onClick={() => onRemove(r.candidate_id)}>remove</button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="compare-total">
                <td>Final score</td>
                {results.map(r => (
                  <td key={r.candidate_id} className={`mono ${r.final_score === best('final') ? 'is-best' : ''}`}>{pct(r.final_score)}</td>
                ))}
              </tr>
              {signals.map(s => (
                <tr key={s.key}>
                  <td><span className="swatch" style={{ background: s.color }} />{s.label}</td>
                  {results.map(r => (
                    <td key={r.candidate_id} className={`mono ${(r.scores[s.key] ?? 0) === best(s.key) ? 'is-best' : ''}`}>{pct(r.scores[s.key])}</td>
                  ))}
                </tr>
              ))}
              <tr>
                <td>Experience</td>
                {results.map(r => <td key={r.candidate_id} className="mono">{r.experience_years} yrs</td>)}
              </tr>
              <tr>
                <td>Matched skills</td>
                {results.map(r => <td key={r.candidate_id}>{r.matched_skills.join(', ') || '—'}</td>)}
              </tr>
              <tr>
                <td>Location</td>
                {results.map(r => <td key={r.candidate_id}>{r.location || '—'}</td>)}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
