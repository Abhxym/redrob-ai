import { useEffect, useMemo } from 'react';
import { X, MapPin, Briefcase, GraduationCap, Star, LoaderCircle, Check } from 'lucide-react';
import { ScoreRing, SignalBars } from './ScoreBits.jsx';
import { parseProfileText, jdMentions, initials } from '../lib/profile.js';

export default function CandidateDrawer({ result, profile, loading, weights, jdText, starred, onStar, onClose }) {
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const p = useMemo(() => parseProfileText(profile?.profile_text || ''), [profile]);
  // Prefer the pipeline's own ontology matches; fall back to literal JD mentions.
  const pipelineMatches = new Set(result.matched_skills.map(s => s.toLowerCase()));
  const isMatch = sk => pipelineMatches.has(sk.toLowerCase()) || jdMentions(jdText, sk);
  const matched = p.skills.filter(isMatch);
  const others = p.skills.filter(sk => !isMatch(sk));
  const title = p.headline || result.headline || result.candidate_id;

  return (
    <div className="drawer-wrap" role="dialog" aria-modal="true" aria-label={`Profile ${result.candidate_id}`}>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-top">
          <span className="avatar avatar-lg" aria-hidden="true">{initials(title)}</span>
          <div className="drawer-id">
            <span className="eyebrow">Rank #{result.rank} · <span className="mono">{result.candidate_id}</span></span>
            <h2>{title}</h2>
            <div className="crow-meta">
              {p.currentRole && <span><Briefcase size={12} /> {p.currentRole}</span>}
              {p.location && <span><MapPin size={12} /> {p.location}</span>}
              {p.experienceYears > 0 && <span>{p.experienceYears} yrs</span>}
            </div>
          </div>
          <div className="drawer-tools">
            <button type="button" className={`icon-btn ${starred ? 'is-on star-on' : ''}`} onClick={onStar} aria-label="Toggle shortlist">
              <Star size={16} fill={starred ? 'currentColor' : 'none'} />
            </button>
            <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
              <X size={16} />
            </button>
          </div>
        </div>

        <div className="drawer-body">
          <section className="dsec dsec-score">
            <ScoreRing value={result.final_score} size={84} />
            <SignalBars scores={result.scores} weights={weights} />
          </section>

          <section className="dsec">
            <h3>Why this rank</h3>
            <ul className="reasons">
              {result.reasoning.map((r, i) => (
                <li key={i}><Check size={14} /> <span>{r}</span></li>
              ))}
            </ul>
          </section>

          {loading && (
            <div className="muted center pad"><LoaderCircle className="spin" size={18} /> Loading profile…</div>
          )}

          {!loading && profile && (
            <>
              {p.skills.length > 0 && (
                <section className="dsec">
                  <h3>Skills <span className="muted small">{matched.length} of {p.skills.length} match the JD</span></h3>
                  <div className="tags">
                    {matched.map(sk => <span key={sk} className="tag tag-match">{sk}</span>)}
                    {others.map(sk => <span key={sk} className="tag">{sk}</span>)}
                  </div>
                </section>
              )}

              {p.assessments.length > 0 && (
                <section className="dsec">
                  <h3>Skill assessments</h3>
                  <div className="assess">
                    {p.assessments.map(a => (
                      <div key={a.skill} className="assess-row">
                        <span>{a.skill}</span>
                        <span className="sigbar-track"><span className="sigbar-fill" style={{ width: `${a.score}%` }} /></span>
                        <span className="mono">{a.score}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {Object.keys(p.signals).length > 0 && (
                <section className="dsec">
                  <h3>Platform signals</h3>
                  <dl className="kv">
                    {Object.entries(p.signals).map(([k, v]) => (
                      <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
                    ))}
                  </dl>
                </section>
              )}

              {p.summary && (
                <section className="dsec">
                  <h3>Summary</h3>
                  <p className="prose">{p.summary}</p>
                </section>
              )}

              {p.history.length > 0 && (
                <section className="dsec">
                  <h3>Career history</h3>
                  <ol className="timeline">
                    {p.history.map((h, i) => (
                      <li key={i}>
                        <div className="tl-head">
                          <strong>{h.title}</strong>
                          {h.company && <span className="muted"> · {h.company}</span>}
                          {h.current && <span className="tag tag-good">Current</span>}
                          {h.months && <span className="muted small mono">{h.months} mo</span>}
                        </div>
                        {h.description && <p className="prose small">{h.description}</p>}
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              {p.education.length > 0 && (
                <section className="dsec">
                  <h3>Education</h3>
                  {p.education.map((e, i) => (
                    <p key={i} className="edu"><GraduationCap size={14} /> {e}</p>
                  ))}
                </section>
              )}

              <details className="dsec raw">
                <summary>Raw profile text</summary>
                <pre>{profile.profile_text}</pre>
              </details>
            </>
          )}
        </div>
      </aside>
    </div>
  );
}
