import { MapPin, Briefcase, Star, GitCompare } from 'lucide-react';
import { ScoreRing, ContributionBar } from './ScoreBits.jsx';
import { initials } from '../lib/profile.js';

export default function CandidateRow({ result, weights, starred, comparing, onStar, onCompare, onOpen }) {
  const title = result.current_title || result.headline || result.candidate_id;

  return (
    <li className={`crow ${result.rank <= 3 ? `crow-top crow-top-${result.rank}` : ''}`}>
      <button type="button" className="crow-main" onClick={onOpen} aria-label={`Open ${result.candidate_id}`}>
        <span className="crow-rank mono">#{result.rank}</span>
        <span className="avatar" aria-hidden="true">{initials(title)}</span>
        <span className="crow-body">
          <span className="crow-title">{title}</span>
          <span className="crow-meta">
            <span className="mono">{result.candidate_id}</span>
            {result.location && <span><MapPin size={12} /> {result.location}</span>}
            {result.experience_years > 0 && <span><Briefcase size={12} /> {result.experience_years} yrs</span>}
            {result.open_to_work && <span className="tag tag-good">Open to work</span>}
          </span>
          <ContributionBar scores={result.scores} weights={weights} />
          {result.matched_skills.length > 0 && (
            <span className="crow-skills">
              {result.matched_skills.slice(0, 5).map(s => <span key={s} className="tag tag-match">{s}</span>)}
              {result.matched_skills.length > 5 && <span className="muted small">+{result.matched_skills.length - 5}</span>}
            </span>
          )}
        </span>
        <ScoreRing value={result.final_score} />
      </button>
      <div className="crow-actions">
        <button
          type="button"
          className={`icon-btn ${starred ? 'is-on star-on' : ''}`}
          onClick={onStar}
          aria-pressed={starred}
          aria-label={starred ? 'Remove from shortlist' : 'Add to shortlist'}
          title="Shortlist"
        >
          <Star size={15} fill={starred ? 'currentColor' : 'none'} />
        </button>
        <button
          type="button"
          className={`icon-btn ${comparing ? 'is-on' : ''}`}
          onClick={onCompare}
          aria-pressed={comparing}
          aria-label={comparing ? 'Remove from comparison' : 'Add to comparison'}
          title="Compare"
        >
          <GitCompare size={15} />
        </button>
      </div>
    </li>
  );
}
