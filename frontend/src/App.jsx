import { useState, useEffect, useMemo, useCallback } from 'react';
import Header from './components/Header.jsx';
import Composer from './components/Composer.jsx';
import Landing from './components/Landing.jsx';
import { RunProgress, RunDetails } from './components/PipelineTracker.jsx';
import CandidateRow from './components/CandidateRow.jsx';
import CandidateDrawer from './components/CandidateDrawer.jsx';
import CompareModal from './components/CompareModal.jsx';
import { rankCandidates, getHealth, getCandidate } from './api.js';
import { effectiveWeights, activeSignals, toCsv } from './lib/profile.js';

const MAX_COMPARE = 3;

export default function App() {
  const [health, setHealth] = useState(null);
  const [offline, setOffline] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastQuery, setLastQuery] = useState(null);
  const [response, setResponse] = useState(null);

  const [query, setQuery] = useState('');
  const [sortKey, setSortKey] = useState('final');
  const [openOnly, setOpenOnly] = useState(false);
  const [shortlistOnly, setShortlistOnly] = useState(false);
  const [starred, setStarred] = useState(() => new Set());
  const [compare, setCompare] = useState([]);
  const [showCompare, setShowCompare] = useState(false);

  const [drawer, setDrawer] = useState(null); // { result, profile, loading }

  // Poll health until the backend has finished loading data, indexes and models.
  const ready = health?.warm_state === 'ready';
  useEffect(() => {
    if (ready || health?.warm_state === 'error') return;
    let cancelled = false;
    const check = () => getHealth()
      .then(h => { if (!cancelled) { setHealth(h); setOffline(false); } })
      .catch(() => { if (!cancelled) setOffline(true); });
    check();
    const id = setInterval(check, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, [ready, health?.warm_state]);

  const info = response?.pipeline_info;
  const weights = useMemo(() => effectiveWeights(info), [info]);
  const signals = useMemo(() => activeSignals(weights), [weights]);

  const runRank = useCallback(async (jdText, topK) => {
    setLoading(true);
    setError(null);
    setLastQuery({ jdText, topK });
    setCompare([]);
    try {
      const data = await rankCandidates(jdText, topK);
      setResponse(data);
      setOffline(false);
    } catch (err) {
      if (!err?.response) setOffline(true);
      setError(err?.response?.data?.detail || err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const openDrawer = useCallback(async result => {
    setDrawer({ result, profile: null, loading: true });
    try {
      const profile = await getCandidate(result.candidate_id);
      setDrawer(d => (d?.result.candidate_id === result.candidate_id ? { ...d, profile, loading: false } : d));
    } catch {
      setDrawer(d => (d ? { ...d, loading: false } : d));
    }
  }, []);

  const toggleStar = id => setStarred(prev => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return next;
  });

  const toggleCompare = id => setCompare(prev =>
    prev.includes(id) ? prev.filter(x => x !== id) : prev.length >= MAX_COMPARE ? [...prev.slice(1), id] : [...prev, id]);

  const results = useMemo(() => response?.results ?? [], [response]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return results
      .filter(r => {
        if (openOnly && !r.open_to_work) return false;
        if (shortlistOnly && !starred.has(r.candidate_id)) return false;
        if (!q) return true;
        const hay = [r.candidate_id, r.headline, r.current_title, r.location, ...r.matched_skills, ...r.reasoning]
          .join(' ').toLowerCase();
        return hay.includes(q);
      })
      .sort((a, b) => (sortKey === 'final'
        ? b.final_score - a.final_score
        : (b.scores[sortKey] ?? 0) - (a.scores[sortKey] ?? 0)));
  }, [results, query, sortKey, openOnly, shortlistOnly, starred]);

  const exportCsv = () => {
    const blob = new Blob([toCsv(visible, weights)], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `redrob-ranking-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const hasResults = results.length > 0;

  return (
    <div className="app">
      <Header health={health} offline={offline} onHome={() => { setResponse(null); setError(null); }} />

      {!hasResults && !loading ? (
        <>
          {error && <div className="alert alert-hero" role="alert">Ranking failed: {error}{offline && '. Is the API running on port 8000?'}</div>}
          <Landing health={health} onSubmit={runRank} loading={loading} notReady={!ready} />
        </>
      ) : (
      <div className="workspace">
        <aside className="sidebar">
          <div className="section">
            <h3 className="label">Job description</h3>
            <Composer onSubmit={runRank} loading={loading} notReady={!ready} compact initialText={lastQuery?.jdText} initialTopK={lastQuery?.topK} />
          </div>

          {loading && <div className="section"><RunProgress /></div>}

          {hasResults && !loading && (
            <>
              <div className="section">
                <h3 className="label">Last run</h3>
                <RunDetails info={info} />
              </div>
              <div className="section">
                <h3 className="label">Weights for this JD</h3>
                <table className="kv-table">
                  <tbody>
                    {signals.map(s => (
                      <tr key={s.key} title={s.hint}>
                        <th><span className="swatch" style={{ background: s.color }} />{s.label}</th>
                        <td className="mono">{Math.round(weights[s.key] * 100)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {info?.ce_blend && (
                  <p className="hint">
                    Final = {Math.round(info.ce_blend.feature * 100)}% feature score + {Math.round(info.ce_blend.cross_encoder * 100)}% cross-encoder.
                  </p>
                )}
              </div>
              {info?.jd_skills?.length > 0 && (
                <div className="section">
                  <h3 className="label">Skills found in JD</h3>
                  <p className="skills-text">{info.jd_skills.join(', ')}</p>
                </div>
              )}
            </>
          )}
        </aside>

        <main className="main">
          {error && (
            <div className="alert" role="alert">
              <span>Ranking failed: {error}{offline && '. Is the API running on port 8000?'}</span>
              {lastQuery && (
                <button type="button" className="btn" onClick={() => runRank(lastQuery.jdText, lastQuery.topK)} disabled={loading}>Retry</button>
              )}
            </div>
          )}

          {loading && !hasResults && <div className="empty"><p className="muted">Working…</p></div>}

          {hasResults && (
            <div className={loading ? 'is-stale' : ''}>
              <div className="stat-row">
                <StatCard label="Profiles searched" value={(info?.corpus_size ?? 0).toLocaleString()} tag="bm25 + faiss" />
                <StatCard label="Top match" value={Math.round(results[0].final_score * 100)} tag="/ 100" />
                <StatCard label="Ranked in" value={info?.latency} tag={info?.jd_type?.replace('_', ' ')} />
              </div>
              <div className="toolbar">
                <span className="summary"><strong>{visible.length}</strong> of top {results.length}</span>
                <span className="toolbar-spacer" />
                <input className="input" value={query} onChange={e => setQuery(e.target.value)} placeholder="Filter" aria-label="Filter results" />
                <select className="input" value={sortKey} onChange={e => setSortKey(e.target.value)} aria-label="Sort by">
                  <option value="final">Sort by final score</option>
                  {signals.map(s => <option key={s.key} value={s.key}>Sort by {s.label.toLowerCase()}</option>)}
                </select>
                <label className="check"><input type="checkbox" checked={openOnly} onChange={e => setOpenOnly(e.target.checked)} /> Open to work</label>
                <label className="check"><input type="checkbox" checked={shortlistOnly} onChange={e => setShortlistOnly(e.target.checked)} /> Starred ({starred.size})</label>
                <button type="button" className="btn" onClick={exportCsv} disabled={!visible.length}>Export CSV</button>
              </div>

              {compare.length > 0 && (
                <div className="selection">
                  <span>{compare.length} selected for comparison</span>
                  <button type="button" className="btn btn-primary" disabled={compare.length < 2} onClick={() => setShowCompare(true)}>Compare</button>
                  <button type="button" className="link" onClick={() => setCompare([])}>Clear</button>
                </div>
              )}

              <div className="table-wrap">
                <table className="results">
                  <thead>
                    <tr>
                      <th className="cell-check" aria-label="Compare" />
                      <th className="num">#</th>
                      <th>Candidate</th>
                      <th className="num">Yrs</th>
                      <th>Matched skills</th>
                      <th>Score breakdown</th>
                      <th className="num">Score</th>
                      <th aria-label="Star" />
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map(r => (
                      <CandidateRow
                        key={r.candidate_id}
                        result={r}
                        weights={weights}
                        starred={starred.has(r.candidate_id)}
                        comparing={compare.includes(r.candidate_id)}
                        selected={drawer?.result.candidate_id === r.candidate_id}
                        onStar={() => toggleStar(r.candidate_id)}
                        onCompare={() => toggleCompare(r.candidate_id)}
                        onOpen={() => openDrawer(r)}
                      />
                    ))}
                  </tbody>
                </table>
                {visible.length === 0 && <p className="muted pad">No candidates match these filters.</p>}
              </div>

              <div className="legend">
                {signals.map(s => <span key={s.key}><span className="swatch" style={{ background: s.color }} />{s.label}</span>)}
              </div>
            </div>
          )}
        </main>
      </div>
      )}

      {showCompare && compare.length > 0 && (
        <CompareModal
          results={compare.map(id => results.find(r => r.candidate_id === id)).filter(Boolean)}
          onRemove={id => setCompare(c => c.filter(x => x !== id))}
          onClose={() => setShowCompare(false)}
        />
      )}

      {drawer && (
        <CandidateDrawer
          result={drawer.result}
          profile={drawer.profile}
          loading={drawer.loading}
          weights={weights}
          jdText={lastQuery?.jdText}
          starred={starred.has(drawer.result.candidate_id)}
          onStar={() => toggleStar(drawer.result.candidate_id)}
          onClose={() => setDrawer(null)}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, tag }) {
  return (
    <article className="card card-flat stat-card">
      <div className="card-top"><span className="diamond" aria-hidden="true" /><span className="rule" />{tag && <span className="tag">{tag}</span>}</div>
      <div className="stat">{value}</div>
      <p className="card-note">{label}</p>
    </article>
  );
}
