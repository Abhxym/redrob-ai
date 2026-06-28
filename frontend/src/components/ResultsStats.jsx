import { Trophy, Users, TrendingUp, Zap, Brain } from 'lucide-react';
import './ResultsStats.css';

export default function ResultsStats({ response }) {
  if (!response) return null;

  const { results, jd_snippet, total_evaluated, pipeline_info } = response;
  const topScore = results.length > 0 ? Math.round(results[0].final_score * 100) : 0;
  const avgScore = results.length > 0
    ? Math.round(results.reduce((acc, r) => acc + r.final_score, 0) / results.length * 100)
    : 0;

  const stats = [
    { icon: <Trophy size={18} />, value: `${topScore}%`, label: 'Top Match Score', color: 'var(--amber)' },
    { icon: <TrendingUp size={18} />, value: `${avgScore}%`, label: 'Avg Score', color: 'var(--emerald)' },
    { icon: <Users size={18} />, value: total_evaluated, label: 'Candidates Ranked', color: 'var(--cyan)' },
    { icon: <Zap size={18} />, value: pipeline_info.latency, label: 'Pipeline Latency', color: 'var(--violet)' },
  ];

  return (
    <div className="results-stats fade-up">
      <div className="stats-header">
        <Brain size={16} className="stats-brain" />
        <div>
          <h2 className="stats-title">Ranking Results</h2>
          <p className="stats-jd">"{jd_snippet}"</p>
        </div>
      </div>

      <div className="stats-grid">
        {stats.map((s, i) => (
          <div key={i} className="stat-card card" style={{ '--stat-color': s.color }}>
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="pipeline-info">
        <span className="pipeline-info-label">Pipeline:</span>
        <span className="pipeline-info-val">{pipeline_info.retrieval}</span>
        <span className="pipeline-sep">·</span>
        <span className="pipeline-info-val">{pipeline_info.scoring}</span>
        <span className="pipeline-sep">·</span>
        <span className="pipeline-info-val pipeline-cost">Cost: {pipeline_info.cost}</span>
      </div>
    </div>
  );
}
