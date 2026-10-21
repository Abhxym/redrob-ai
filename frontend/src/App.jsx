import { useState, useEffect, useMemo, useCallback, lazy, Suspense } from 'react';
import { CircleAlert, RotateCcw, Search, Download, GitCompare, Database, Zap, Gauge, Layers } from 'lucide-react';
import Header from './components/Header.jsx';
import Composer from './components/Composer.jsx';
import PipelineTracker from './components/PipelineTracker.jsx';
import CandidateRow from './components/CandidateRow.jsx';
import CandidateDrawer from './components/CandidateDrawer.jsx';
import { rankCandidates, getHealth, getCandidate } from './api.js';
import { effectiveWeights, activeSignals, toCsv, pct } from './lib/profile.js';

// Recharts is only needed for the comparison radar, so load it on demand.
const CompareModal = lazy(() => import('./components/CompareModal.jsx'));

const MAX_COMPARE = 3;

function initialTheme() {
  try {
    const saved = localStorage.getItem('redrob-theme');
    if (saved) return saved;
  } catch { /* storage unavailable */ }
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export default function App() {
  const [theme, setTheme] = useState(initialTheme);
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

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('redrob-theme', theme); } catch { /* ignore */ }
  }, [theme]);

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
  const sorts = useMemo(() => [{ key: 'final', label: 'Final score' }, ...activeSignals(weights)], [weights]);

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
  const avg = hasResults ? results.reduce((s, r) => s + r.final_score, 0) / results.length : 0;

  return (
    <div className="app">
      <Header health={health} offline={offline} theme={theme} onToggleTheme={() => setTheme(t => (t === 'dark' ? 'light' : 'dark'))} />

      <main className={`layout ${hasResults || loading ? 'layout-split' : 'layout-hero'}`}>
        {!hasResults && !loading && (
          <section className="hero">
            <span className="eyebrow">Explainable candidate ranking</span>
            <h1>Find the right engineers, <span className="grad">and see exactly why.</span></h1>
            <p className="muted hero-sub">
              Hybrid BM25 + FAISS retrieval fused with Reciprocal Rank Fusion, scored on five JD-aware signals,
              then re-ranked by a cross-encoder. Deterministic, offline, CPU-only, zero LLM cost.
            </p>
          </section>
        )}

        <div className="side">
          <Composer onSubmit={runRank} loading={loading} compact={hasResults} notReady={!ready} />
          <PipelineTracker loading={loading} done={hasResults && !loading} info={info} />
          {hasResults && (
            <section className="card weights">
              <div className="weights-head">
                <span className="eyebrow">Share of final score</span>
                {info?.jd_type && <span className="tag">{info.jd_type.replace('_', ' ')} JD</span>}
              </div>
              {activeSignals(weights).map(s => (
                <div key={s.key} className="weight-row" title={s.hint}>
                  <span className="swatch" style={{ background: s.color }} />
                  <span>{s.label}</span>
                  <span className="weight-bar"><span style={{ width: `${weights[s.key] * 100 * 2.5}%`, background: s.color }} /></span>
                  <span className="mono small">{Math.round(weights[s.key] * 100)}%</span>
                </div>
              ))}
              {info?.jd_skills?.length > 0 && (
                <div className="jd-skills">
                  <span className="eyebrow">Skills detected in JD</span>
                  <div className="tags">{info.jd_skills.map(s => <span key={s} className="tag">{s}</span>)}</div>
                </div>
              )}
            </section>
          )}
        </div>

        <div className="results" id="results">
          {error && (
            <div className="banner banner-error" role="alert">
              <CircleAlert size={16} />
              <span>Ranking failed: {error}{offline && ' — is the API running on port 8000?'}</span>
              {lastQuery && (
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => runRank(lastQuery.jdText, lastQuery.topK)} disabled={loading}>
                  <RotateCcw size={13} /> Retry
                </button>
              )}
            </div>
          )}

          {loading && (
            <ul className="crow-list" aria-busy="true">
              {Array.from({ length: 6 }, (_, i) => <li key={i} className="crow skeleton" />)}
            </ul>
          )}

          {hasResults && !loading && (
            <>
              <div className="stats">
                <Stat icon={<Database size={15} />} label="Searched" value={(info?.corpus_size ?? 0).toLocaleString()} />
                <Stat icon={<Gauge size={15} />} label="Top match" value={pct(results[0].final_score)} />
                <Stat icon={<Layers size={15} />} label={`Avg of top ${results.length}`} value={pct(avg)} />
                <Stat icon={<Zap size={15} />} label="Latency" value={info?.latency ?? '—'} />
              </div>

              <div className="toolbar">
                <label className="search">
                  <Search size={14} />
                  <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Filter by skill, role, location…" aria-label="Filter results" />
                </label>
                <select value={sortKey} onChange={e => setSortKey(e.target.value)} aria-label="Sort by">
                  {sorts.map(s => <option key={s.key} value={s.key}>Sort: {s.label}</option>)}
                </select>
                <button type="button" className={`pill ${openOnly ? 'pill-on' : ''}`} onClick={() => setOpenOnly(v => !v)} aria-pressed={openOnly}>Open to work</button>
                <button type="button" className={`pill ${shortlistOnly ? 'pill-on' : ''}`} onClick={() => setShortlistOnly(v => !v)} aria-pressed={shortlistOnly}>★ Starred ({starred.size})</button>
                <span className="toolbar-spacer" />
                <button type="button" className="btn btn-ghost btn-sm" onClick={exportCsv} disabled={!visible.length}>
                  <Download size={14} /> CSV
                </button>
              </div>

              <div className="legend" aria-label="Signal colors">
                {activeSignals(weights).map(s => (
                  <span key={s.key}><span className="swatch" style={{ background: s.color }} />{s.label}</span>
                ))}
              </div>

              {visible.length === 0 ? (
                <div className="empty card">No candidates match these filters.</div>
              ) : (
                <ul className="crow-list">
                  {visible.map(r => (
                    <CandidateRow
                      key={r.candidate_id}
                      result={r}
                      weights={weights}
                      starred={starred.has(r.candidate_id)}
                      comparing={compare.includes(r.candidate_id)}
                      onStar={() => toggleStar(r.candidate_id)}
                      onCompare={() => toggleCompare(r.candidate_id)}
                      onOpen={() => openDrawer(r)}
                    />
                  ))}
                </ul>
              )}
            </>
          )}

          {!hasResults && !loading && !error && (
            <div className="howto">
              {[
                ['01', 'Retrieve', 'BM25 catches exact skill keywords; FAISS catches meaning. RRF fuses both ranked lists into a top 100.'],
                ['02', 'Score', 'Semantic fit, ontology-matched skills, experience, behavior and career growth, with weights tuned to the JD type.'],
                ['03', 'Re-rank & explain', 'A cross-encoder reads the JD and each profile together, blended 70/30 with the feature score. Every rank comes with reasons.'],
              ].map(([n, t, d]) => (
                <div key={n} className="card howto-card">
                  <span className="mono howto-n">{n}</span>
                  <h3>{t}</h3>
                  <p className="muted small">{d}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {compare.length > 0 && (
        <div className="tray">
          <GitCompare size={15} />
          <span>{compare.length} selected</span>
          <span className="mono muted small">{compare.join(' · ')}</span>
          <button type="button" className="btn btn-primary btn-sm" disabled={compare.length < 2} onClick={() => setShowCompare(true)}>Compare</button>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setCompare([])}>Clear</button>
        </div>
      )}

      {showCompare && compare.length > 0 && (
        <Suspense fallback={null}>
          <CompareModal
            results={compare.map(id => results.find(r => r.candidate_id === id)).filter(Boolean)}
            onRemove={id => setCompare(c => c.filter(x => x !== id))}
            onClose={() => setShowCompare(false)}
          />
        </Suspense>
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

function Stat({ icon, label, value }) {
  return (
    <div className="stat card">
      <span className="stat-label muted small">{icon}{label}</span>
      <span className="stat-value mono">{value}</span>
    </div>
  );
}
