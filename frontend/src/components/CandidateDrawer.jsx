import { useEffect, useMemo } from 'react';
import { X, Star } from 'lucide-react';
import { SignalTable } from './ScoreBits.jsx';
import { parseProfileText, jdMentions, pct } from '../lib/profile.js';

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

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={`Candidate ${result.candidate_id}`}>
      <div className="scrim" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-head">
          <div>
            <div className="sub mono">Rank {result.rank} · {result.candidate_id}</div>
            <h2>{result.current_title || p.headline}</h2>
            <div className="sub">
              {[p.currentRole, p.location, `${result.experience_years} yrs experience`].filter(Boolean).join(' · ')}
            </div>
          </div>
          <div className="drawer-tools">
            <button type="button" className={`star ${starred ? 'is-on' : ''}`} onClick={onStar} aria-label="Toggle star">
              <Star size={15} fill={starred ? 'currentColor' : 'none'} />
            </button>
            <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><X size={15} /></button>
          </div>
        </div>

        <div className="drawer-body">
          <section className="dsec">
            <div className="score-line">
              <span className="score-big mono">{pct(result.final_score)}</span>
              <span className="muted">final score, out of 100</span>
            </div>
            <SignalTable scores={result.scores} weights={weights} />
          </section>

          <section className="dsec">
            <h3>Why this rank</h3>
            <ul className="plain-list">
              {result.reasoning.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </section>

          {loading && <p className="muted">Loading profile…</p>}

          {!loading && profile && (
            <>
              {p.skills.length > 0 && (
                <section className="dsec">
                  <h3>Skills <span className="muted normal">· {matched.length} of {p.skills.length} match the JD</span></h3>
                  <p className="skills-text">
                    {matched.map((sk, i) => <span key={sk}><mark>{sk}</mark>{i < matched.length - 1 || others.length ? ', ' : ''}</span>)}
                    {others.join(', ')}
                  </p>
                </section>
              )}

              {p.assessments.length > 0 && (
                <section className="dsec">
                  <h3>Skill assessments</h3>
                  <table className="kv-table">
                    <tbody>
                      {p.assessments.map(a => <tr key={a.skill}><th>{a.skill}</th><td className="mono">{a.score}/100</td></tr>)}
                    </tbody>
                  </table>
                </section>
              )}

              {Object.keys(p.signals).length > 0 && (
                <section className="dsec">
                  <h3>Platform signals</h3>
                  <table className="kv-table">
                    <tbody>
                      {Object.entries(p.signals).map(([k, v]) => <tr key={k}><th>{k}</th><td>{v}</td></tr>)}
                    </tbody>
                  </table>
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
                  <h3>Experience</h3>
                  {p.history.map((h, i) => (
                    <div key={i} className="job">
                      <div className="job-head">
                        <strong>{h.title}</strong>{h.company && <span> · {h.company}</span>}
                        <span className="muted mono"> {h.current ? 'current' : ''}{h.current && h.months ? ', ' : ''}{h.months ? `${h.months} mo` : ''}</span>
                      </div>
                      {h.description && <p className="prose">{h.description}</p>}
                    </div>
                  ))}
                </section>
              )}

              {p.education.length > 0 && (
                <section className="dsec">
                  <h3>Education</h3>
                  <ul className="plain-list">{p.education.map((e, i) => <li key={i}>{e}</li>)}</ul>
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
