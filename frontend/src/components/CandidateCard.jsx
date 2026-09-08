import { useState, useEffect, useRef } from 'react';
import { MapPin, Clock, Briefcase, ChevronDown, ChevronUp, ExternalLink, CheckCircle2 } from 'lucide-react';
import './CandidateCard.css';

const SCORE_DIMS = [
  { key: 'semantic',   label: 'Semantic',   weight: '40%' },
  { key: 'skills',     label: 'Skills',     weight: '25%' },
  { key: 'experience', label: 'Experience', weight: '15%' },
  { key: 'behavior',   label: 'Behavior',   weight: '10%' },
  { key: 'career',     label: 'Career',     weight: '10%' },
];

function getScoreColor(val) {
  if (val >= 0.7) return 'var(--score-high)';
  if (val >= 0.4) return 'var(--score-mid)';
  return 'var(--score-low)';
}

function getRankClass(rank) {
  if (rank === 1) return 'rank-1';
  if (rank === 2) return 'rank-2';
  if (rank === 3) return 'rank-3';
  return 'rank-n';
}

function getMatchBadge(rank, score) {
  if (rank <= 3) return { label: '⭐ Top Match', cls: 'badge-amber' };
  if (score >= 0.7) return { label: 'Strong Match', cls: 'badge-emerald' };
  if (score >= 0.5) return { label: 'Good Match', cls: 'badge-cyan' };
  return { label: 'Potential Match', cls: 'badge-violet' };
}

function ScoreBar({ label, value, weight, animate }) {
  const color = getScoreColor(value);
  const pct = Math.round(value * 100);
  return (
    <div className="score-bar-wrap">
      <span className="score-label">{label}</span>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{
            width: animate ? `${pct}%` : '0%',
            background: `linear-gradient(90deg, ${color}aa, ${color})`,
          }}
        />
      </div>
      <span className="score-value" style={{ color }}>{pct}%</span>
      <span className="score-weight">{weight}</span>
    </div>
  );
}

export default function CandidateCard({ result, index, onViewProfile }) {
  const [expanded, setExpanded] = useState(false);
  const [animate, setAnimate] = useState(false);
  const cardRef = useRef(null);

  const { rank, candidate_id, final_score, scores, reasoning } = result;
  const finalPct = Math.round(final_score * 100);

  // Animate bars when card enters viewport
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setAnimate(true); },
      { threshold: 0.2 }
    );
    if (cardRef.current) observer.observe(cardRef.current);
    return () => observer.disconnect();
  }, []);

  const rankClass = getRankClass(rank);
  const scoreColor = getScoreColor(final_score);

  return (
    <article
      ref={cardRef}
      className="candidate-card card fade-up"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* ─ Header ─ */}
      <div className="ccard-header">
        <div className={`rank-badge ${rankClass}`}>{rank}</div>

        <div className="ccard-identity">
          <div className="ccard-id">{candidate_id}</div>
          <div className="ccard-meta">
            {(() => { const { label, cls } = getMatchBadge(rank, final_score); return <span className={`badge ${cls}`}>{label}</span>; })()}
          </div>
        </div>

        {/* Final Score ring */}
        <div className="final-score-ring" style={{ '--score-pct': `${finalPct}%`, '--score-color': scoreColor }}>
          <svg className="ring-svg" viewBox="0 0 36 36">
            <circle className="ring-bg" cx="18" cy="18" r="15.9" />
            <circle
              className="ring-fill"
              cx="18" cy="18" r="15.9"
              strokeDasharray={`${animate ? finalPct : 0} 100`}
              style={{ stroke: scoreColor }}
            />
          </svg>
          <div className="ring-label">
            <span className="ring-value">{finalPct}</span>
            <span className="ring-pct">%</span>
          </div>
        </div>
      </div>

      {/* ─ Score Bars ─ */}
      <div className="ccard-scores">
        {SCORE_DIMS.map(dim => (
          <ScoreBar
            key={dim.key}
            label={dim.label}
            value={scores[dim.key]}
            weight={dim.weight}
            animate={animate}
          />
        ))}
      </div>

      {/* ─ Reasoning ─ */}
      <div className="ccard-reasons">
        {reasoning.slice(0, expanded ? reasoning.length : 3).map((r, i) => (
          <div key={i} className="reason-chip">
            <CheckCircle2 size={12} className="reason-icon" />
            <span>{r}</span>
          </div>
        ))}
      </div>

      {/* ─ Footer ─ */}
      <div className="ccard-footer">
        <button
          type="button"
          className="expand-btn"
          onClick={() => setExpanded(e => !e)}
          aria-expanded={expanded}
        >
          {expanded ? <><ChevronUp size={13}/> Less</> : <><ChevronDown size={13}/> {reasoning.length > 3 ? `+${reasoning.length - 3} more` : 'More'}</>}
        </button>

        <button
          type="button"
          className="btn btn-ghost btn-sm profile-btn"
          onClick={() => onViewProfile(candidate_id)}
        >
          <ExternalLink size={13} />
          View Profile
        </button>
      </div>
    </article>
  );
}
