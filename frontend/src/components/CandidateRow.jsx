import { Star } from 'lucide-react';
import { ContributionBar } from './ScoreBits.jsx';
import { pct } from '../lib/profile.js';

export default function CandidateRow({ result, weights, starred, comparing, selected, onStar, onCompare, onOpen }) {
  const title = result.current_title || result.headline || result.candidate_id;

  return (
    <tr className={`row ${selected ? 'is-selected' : ''}`} onClick={onOpen}>
      <td className="cell-check" onClick={e => e.stopPropagation()}>
        <input type="checkbox" checked={comparing} onChange={onCompare} aria-label={`Compare ${result.candidate_id}`} />
      </td>
      <td className="num mono muted">{result.rank}</td>
      <td className="cell-name">
        <button type="button" className="name-link" onClick={e => { e.stopPropagation(); onOpen(); }}>{title}</button>
        <div className="sub">
          <span className="mono">{result.candidate_id}</span>
          {result.location && <span>{result.location}</span>}
          {result.open_to_work && <span className="flag">Open to work</span>}
        </div>
      </td>
      <td className="num mono">{result.experience_years}</td>
      <td className="cell-skills" title={result.matched_skills.join(', ')}>
        {result.matched_skills.join(', ') || <span className="muted">—</span>}
      </td>
      <td className="cell-bar"><ContributionBar scores={result.scores} weights={weights} /></td>
      <td className="num mono strong">{pct(result.final_score)}</td>
      <td className="cell-star" onClick={e => e.stopPropagation()}>
        <button
          type="button"
          className={`star ${starred ? 'is-on' : ''}`}
          onClick={onStar}
          aria-pressed={starred}
          aria-label={starred ? 'Unstar' : 'Star'}
        >
          <Star size={14} fill={starred ? 'currentColor' : 'none'} />
        </button>
      </td>
    </tr>
  );
}
