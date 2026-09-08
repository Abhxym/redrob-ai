import { Cpu, Zap, DollarSign } from 'lucide-react';
import './Navbar.css';

export default function Navbar({ health, isOffline }) {
  return (
    <header className="navbar">
      <div className="container">
        <div className="navbar-inner">
          {/* Brand */}
          <div className="nav-brand">
            <div className="nav-logo">
              <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
                <rect width="32" height="32" rx="8" fill="#0f172a"/>
                <circle cx="16" cy="16" r="8" stroke="#06b6d4" strokeWidth="2" fill="none"/>
                <circle cx="16" cy="16" r="3" fill="#06b6d4"/>
                <line x1="16" y1="4" x2="16" y2="8" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round"/>
                <line x1="16" y1="24" x2="16" y2="28" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round"/>
                <line x1="4" y1="16" x2="8" y2="16" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round"/>
                <line x1="24" y1="16" x2="28" y2="16" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <div>
              <span className="brand-name">RedRob <span className="brand-ai">AI</span></span>
              <span className="brand-sub">Recruiter</span>
            </div>
          </div>

          {/* Status pills */}
          <div className="nav-pills">
            {/* API connectivity indicator */}
            {isOffline ? (
              <div className="status-pill status-pill-offline">
                <span className="status-dot status-dot-offline" />
                <span>API Offline</span>
              </div>
            ) : health ? (
              <>
                <div className="status-pill">
                  <span className="status-dot" />
                  <span>{health.candidates_loaded} candidates</span>
                </div>
                <div className="status-pill hide-mobile">
                  <Zap size={12} />
                  <span>4-200ms</span>
                </div>
                <div className="status-pill hide-mobile">
                  <DollarSign size={12} />
                  <span>$0 cost</span>
                </div>
                <div className="status-pill hide-mobile">
                  <Cpu size={12} />
                  <span>BM25 + FAISS</span>
                </div>
              </>
            ) : (
              <div className="status-pill status-pill-connecting">
                <span className="status-dot status-dot-connecting" />
                <span>Connecting…</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
