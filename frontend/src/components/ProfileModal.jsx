import { X, User, MapPin, Clock, Briefcase, Code, CheckCircle2, XCircle, Star, Github } from 'lucide-react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip,
} from 'recharts';
import './ProfileModal.css';

function getScoreColor(val) {
  if (val >= 0.7) return 'var(--score-high)';
  if (val >= 0.4) return 'var(--score-mid)';
  return 'var(--score-low)';
}

function parseProfileText(text) {
  const lines = text ? text.split('\n') : [];
  const result = {
    headline: '', currentRole: '', location: '', experience: '',
    summary: '', skills: [], certifications: [], career: [],
    education: [], signals: {}, assessments: [],
  };

  let section = null;
  let summaryLines = [];

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;

    if (line.startsWith('Headline:')) { result.headline = line.replace('Headline:', '').trim(); continue; }
    if (line.startsWith('Current Role:')) { result.currentRole = line.replace('Current Role:', '').trim(); continue; }
    if (line.startsWith('Location:')) { result.location = line.replace('Location:', '').trim(); continue; }
    if (line.startsWith('Experience:')) { result.experience = line.replace('Experience:', '').trim(); continue; }
    if (line === 'Summary:') { section = 'summary'; continue; }
    if (line === 'Skills:') { section = 'skills'; continue; }
    if (line === 'Certifications:') { section = 'certs'; continue; }
    if (line === 'Career History:') { section = 'career'; continue; }
    if (line === 'Education:') { section = 'education'; continue; }
    if (line === 'Platform Signals:') { section = 'signals'; continue; }
    if (line === 'Skill Assessments:') { section = 'assessments'; continue; }

    switch (section) {
      case 'summary': summaryLines.push(line); break;
      case 'skills':
        result.skills = line.split(',').map(s => s.trim()).filter(Boolean);
        section = null;
        break;
      case 'certs':
        if (line.startsWith('-')) result.certifications.push(line.replace(/^-\s*/, ''));
        break;
      case 'career':
        if (line.startsWith('-')) result.career.push({ title: line.replace(/^-\s*/, ''), desc: [] });
        else if (result.career.length && line.length > 0) result.career[result.career.length - 1].desc.push(line);
        break;
      case 'education':
        if (line.startsWith('-')) result.education.push(line.replace(/^-\s*/, ''));
        break;
      case 'signals':
        // e.g. "Open to work: True | Notice: 60 days | ..."
        const signalParts = line.split('|');
        signalParts.forEach(p => {
          const [k, v] = p.split(':').map(s => s.trim());
          if (k && v !== undefined) result.signals[k] = v;
        });
        break;
      case 'assessments':
        const asmParts = line.split(',');
        asmParts.forEach(a => {
          const [k, v] = a.split(':').map(s => s.trim());
          if (k && v) result.assessments.push({ skill: k, score: parseInt(v) || 0 });
        });
        break;
    }
  }

  result.summary = summaryLines.join(' ');
  return result;
}

export default function ProfileModal({ candidate, result, onClose }) {
  if (!candidate) return null;

  const parsed = parseProfileText(candidate.profile_text);

  // Radar chart data
  const radarData = result ? [
    { subject: 'Semantic', value: Math.round(result.scores.semantic * 100) },
    { subject: 'Skills',   value: Math.round(result.scores.skills * 100) },
    { subject: 'Experience', value: Math.round(result.scores.experience * 100) },
    { subject: 'Behavior', value: Math.round(result.scores.behavior * 100) },
    { subject: 'Career',   value: Math.round(result.scores.career * 100) },
  ] : null;

  return (
    <div className="modal-backdrop fade-in" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-panel fade-up">
        {/* Header */}
        <div className="modal-header">
          <div className="modal-identity">
            <div className="modal-avatar">
              <User size={24} />
            </div>
            <div>
              <div className="modal-id">{candidate.candidate_id}</div>
              <div className="modal-headline">{parsed.headline || candidate.headline}</div>
            </div>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Left column */}
          <div className="modal-left">
            {/* Quick info */}
            <div className="modal-section">
              {parsed.location && (
                <div className="modal-info-row">
                  <MapPin size={13} className="info-icon" />
                  <span>{parsed.location}</span>
                </div>
              )}
              {parsed.currentRole && (
                <div className="modal-info-row">
                  <Briefcase size={13} className="info-icon" />
                  <span>{parsed.currentRole}</span>
                </div>
              )}
              {parsed.experience && (
                <div className="modal-info-row">
                  <Clock size={13} className="info-icon" />
                  <span>{parsed.experience}</span>
                </div>
              )}
            </div>

            {/* Platform signals */}
            {Object.keys(parsed.signals).length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title">Platform Signals</h4>
                <div className="signals-grid">
                  {Object.entries(parsed.signals).map(([k, v]) => {
                    const isPositive = v.toLowerCase().includes('true') || (parseFloat(v) > 50);
                    return (
                      <div key={k} className="signal-row">
                        <span className="signal-key">{k}</span>
                        <span className={`signal-val ${isPositive ? 'positive' : ''}`}>{v}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Skills */}
            {parsed.skills.length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title"><Code size={13}/> Skills</h4>
                <div className="skills-cloud">
                  {parsed.skills.map((s, i) => (
                    <span key={i} className="skill-tag">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Assessments */}
            {parsed.assessments.length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title"><Star size={13}/> Skill Assessments</h4>
                <div className="assessments">
                  {parsed.assessments.map((a, i) => (
                    <div key={i} className="assessment-row">
                      <span className="assessment-skill">{a.skill}</span>
                      <div className="assessment-bar-track">
                        <div
                          className="assessment-bar-fill"
                          style={{
                            width: `${a.score}%`,
                            background: getScoreColor(a.score / 100),
                          }}
                        />
                      </div>
                      <span className="assessment-score">{a.score}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Education */}
            {parsed.education.length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title">Education</h4>
                {parsed.education.map((e, i) => (
                  <div key={i} className="edu-item">{e}</div>
                ))}
              </div>
            )}

            {/* Certifications */}
            {parsed.certifications.length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title">Certifications</h4>
                {parsed.certifications.map((c, i) => (
                  <div key={i} className="cert-item">
                    <CheckCircle2 size={12} style={{ color: 'var(--emerald)' }} />
                    {c}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right column */}
          <div className="modal-right">
            {/* Score radar */}
            {radarData && (
              <div className="modal-section">
                <h4 className="modal-section-title">AI Score Breakdown</h4>
                <div className="modal-final-score">
                  Final Score: <strong style={{ color: getScoreColor(result.final_score) }}>
                    {Math.round(result.final_score * 100)}%
                  </strong>
                  <span className="modal-rank">Rank #{result.rank}</span>
                </div>
                <div className="radar-wrap">
                  <ResponsiveContainer width="100%" height={220}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="var(--border)" />
                      <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: 'var(--text-secondary)', fontSize: 11 }}
                      />
                      <Radar
                        name="Score"
                        dataKey="value"
                        stroke="var(--cyan)"
                        fill="var(--cyan)"
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                      <Tooltip
                        contentStyle={{
                          background: 'var(--bg-elevated)',
                          border: '1px solid var(--border)',
                          borderRadius: '8px',
                          color: 'var(--text-primary)',
                          fontSize: '12px',
                        }}
                        formatter={v => [`${v}%`, 'Score']}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Reasoning */}
            {result && result.reasoning.length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title">AI Reasoning</h4>
                <div className="reasoning-list">
                  {result.reasoning.map((r, i) => (
                    <div key={i} className="reasoning-item">
                      <CheckCircle2 size={13} className="reason-icon" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Career history */}
            {parsed.career.length > 0 && (
              <div className="modal-section">
                <h4 className="modal-section-title">Career History</h4>
                <div className="career-list">
                  {parsed.career.slice(0, 4).map((c, i) => (
                    <div key={i} className="career-item">
                      <div className="career-bullet" />
                      <div>
                        <div className="career-title">{c.title}</div>
                        {c.desc.length > 0 && (
                          <div className="career-desc">{c.desc.slice(0, 2).join(' ').slice(0, 180)}…</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Summary */}
            {parsed.summary && (
              <div className="modal-section">
                <h4 className="modal-section-title">Summary</h4>
                <p className="modal-summary">{parsed.summary}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
