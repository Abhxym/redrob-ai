import { useState, useEffect, useCallback } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import Navbar from './components/Navbar.jsx';
import JDInput from './components/JDInput.jsx';
import ResultsStats from './components/ResultsStats.jsx';
import CandidateCard from './components/CandidateCard.jsx';
import ProfileModal from './components/ProfileModal.jsx';
import { rankCandidates, getHealth, getCandidate } from './api.js';
import './App.css';

export default function App() {
  const [health, setHealth] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  // Profile modal
  const [modalCandidate, setModalCandidate] = useState(null);
  const [modalResult, setModalResult] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Load health on mount
  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => {}); // silently fail - API might not be running
  }, []);

  const handleSubmit = useCallback(async (jdText, topK) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);
    try {
      const data = await rankCandidates(jdText, topK);
      setResponse(data);
      // Scroll to results
      setTimeout(() => {
        document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Unknown error';
      setError(`Failed to rank candidates: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleViewProfile = useCallback(async (candidateId) => {
    setModalLoading(true);
    // Find result data
    const resultData = response?.results?.find(r => r.candidate_id === candidateId) || null;
    setModalResult(resultData);
    try {
      const candidate = await getCandidate(candidateId);
      setModalCandidate(candidate);
    } catch (err) {
      setModalCandidate({ candidate_id: candidateId, profile_text: '' });
    } finally {
      setModalLoading(false);
    }
  }, [response]);

  const handleCloseModal = () => {
    setModalCandidate(null);
    setModalResult(null);
  };

  return (
    <div className="app">
      {/* Ambient background */}
      <div className="app-bg" aria-hidden="true">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-grid" />
      </div>

      <Navbar health={health} />

      <main className="app-main">
        <div className="container">
          {/* JD Input */}
          <JDInput onSubmit={handleSubmit} isLoading={isLoading} />

          {/* Error state */}
          {error && (
            <div className="error-banner fade-in">
              <AlertCircle size={16} />
              <span>{error}</span>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setError(null)}
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Loading skeleton */}
          {isLoading && (
            <div className="loading-section fade-in" aria-label="Loading results">
              <div className="loading-header">
                <div className="spinner" />
                <span>Running AI pipeline…</span>
              </div>
              <div className="skeleton-grid">
                {[1, 2, 3].map(i => (
                  <div key={i} className="skeleton-card card">
                    <div className="skeleton-row">
                      <div className="skeleton skel-circle" />
                      <div className="skeleton-lines">
                        <div className="skeleton skel-line skel-w-60" />
                        <div className="skeleton skel-line skel-w-40" />
                      </div>
                      <div className="skeleton skel-ring" />
                    </div>
                    <div className="skeleton skel-block" />
                    <div className="skeleton skel-block skel-short" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {response && !isLoading && (
            <section id="results-section">
              <ResultsStats response={response} />

              <div className="results-grid" role="list" aria-label="Ranked candidates">
                {response.results.map((result, idx) => (
                  <CandidateCard
                    key={result.candidate_id}
                    result={result}
                    index={idx}
                    onViewProfile={handleViewProfile}
                  />
                ))}
              </div>

              {/* Re-run button */}
              <div className="rerun-wrap">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => { setResponse(null); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                >
                  <RefreshCw size={14} />
                  New Search
                </button>
              </div>
            </section>
          )}

          {/* Empty state */}
          {!response && !isLoading && !error && (
            <div className="hero-empty fade-in">
              <div className="hero-glow" />
              <div className="hero-stats">
                {[
                  { val: 'BM25 + FAISS', label: 'Hybrid Retrieval' },
                  { val: '5-Signal', label: 'Multi-Dimension Scoring' },
                  { val: '$0', label: 'Zero LLM Cost' },
                  { val: '<200ms', label: 'End-to-End Latency' },
                ].map((s, i) => (
                  <div key={i} className="hero-stat">
                    <div className="hero-stat-val">{s.val}</div>
                    <div className="hero-stat-label">{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="container">
          <span>RedRob AI Recruiter · Production-grade candidate ranking · 85% accuracy · $0 inference cost</span>
        </div>
      </footer>

      {/* Profile modal */}
      {(modalCandidate || modalLoading) && (
        <ProfileModal
          candidate={modalCandidate}
          result={modalResult}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}
