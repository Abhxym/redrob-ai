import { activeSignals, pct } from '../lib/profile.js';

// Stacked bar: each segment is signal score × effective weight, so the bar's length is the final score.
export function ContributionBar({ scores, weights }) {
  return (
    <div className="contrib" role="img" aria-label="Contribution of each signal to the final score">
      {activeSignals(weights).map(s => {
        const w = (scores[s.key] ?? 0) * weights[s.key] * 100;
        return (
          <span
            key={s.key}
            style={{ width: `${w}%`, background: s.color }}
            title={`${s.label}: ${pct(scores[s.key])} × ${Math.round(weights[s.key] * 100)}% = ${w.toFixed(1)}`}
          />
        );
      })}
    </div>
  );
}

export function SignalTable({ scores, weights }) {
  const signals = activeSignals(weights);
  return (
    <table className="signal-table">
      <thead>
        <tr><th>Signal</th><th className="num">Score</th><th className="num">Weight</th><th className="num">Points</th><th /></tr>
      </thead>
      <tbody>
        {signals.map(s => {
          const v = scores[s.key] ?? 0;
          return (
            <tr key={s.key} title={s.hint}>
              <td><span className="swatch" style={{ background: s.color }} />{s.label}</td>
              <td className="num mono">{pct(v)}</td>
              <td className="num mono">{Math.round(weights[s.key] * 100)}%</td>
              <td className="num mono">{(v * weights[s.key] * 100).toFixed(1)}</td>
              <td className="bar-cell"><span className="bar"><span style={{ width: `${pct(v)}%`, background: s.color }} /></span></td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
