import { activeSignals, pct } from '../lib/profile.js';

export function ScoreRing({ value, size = 52 }) {
  const stroke = 5;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(1, value ?? 0));
  const tone = v >= 0.75 ? 'high' : v >= 0.55 ? 'mid' : 'low';
  return (
    <div className={`ring ring-${tone}`} style={{ width: size, height: size }} aria-label={`Match score ${pct(v)} out of 100`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-track" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="ring-value"
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - v)}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <span className="ring-label mono">{pct(v)}</span>
    </div>
  );
}

// Stacked bar: each segment is signal score × effective weight, so the bar's length is the final score.
export function ContributionBar({ scores, weights }) {
  return (
    <div className="contrib" role="img" aria-label="Weighted contribution of each signal">
      {activeSignals(weights).map(s => {
        const w = (scores[s.key] ?? 0) * weights[s.key] * 100;
        return (
          <span
            key={s.key}
            className="contrib-seg"
            style={{ width: `${w}%`, background: s.color }}
            title={`${s.label}: ${pct(scores[s.key])} × ${Math.round(weights[s.key] * 100)}% = ${w.toFixed(1)} pts`}
          />
        );
      })}
    </div>
  );
}

export function SignalBars({ scores, weights }) {
  return (
    <div className="sigbars">
      {activeSignals(weights).map(s => (
        <div key={s.key} className="sigbar" title={s.hint}>
          <span className="sigbar-label">
            <span className="swatch" style={{ background: s.color }} />
            {s.label}
            <span className="muted mono small">×{Math.round(weights[s.key] * 100)}%</span>
          </span>
          <span className="sigbar-track">
            <span className="sigbar-fill" style={{ width: `${pct(scores[s.key])}%`, background: s.color }} />
          </span>
          <span className="mono sigbar-val">{pct(scores[s.key])}</span>
        </div>
      ))}
    </div>
  );
}
