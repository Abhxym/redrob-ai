import { Moon, Sun, Cpu, CodeXml } from 'lucide-react';

export default function Header({ health, offline, theme, onToggleTheme }) {
  const warm = health?.warm_state;
  const status = offline ? 'offline'
    : !health ? 'connecting'
    : warm === 'ready' ? 'online'
    : warm === 'error' ? 'offline'
    : 'connecting';
  const label = {
    offline: warm === 'error' ? 'Pipeline failed to load' : 'API offline',
    online: `${(health?.candidates_loaded ?? 0).toLocaleString()} candidates indexed`,
    connecting: health ? 'Warming up models & indexes…' : 'Connecting…',
  }[status];

  return (
    <header className="header">
      <div className="header-inner">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">R</span>
          <span className="brand-name">RedRob<span className="brand-accent">AI</span></span>
          <span className="brand-tag">Recruiter Console</span>
        </a>

        <div className="header-right">
          <span className="chip chip-quiet" title="No LLM calls. Deterministic, CPU-only ranking.">
            <Cpu size={13} /> CPU-only · No LLM
          </span>
          <span className={`status status-${status}`} title={health?.error || undefined}>
            <span className="status-dot" />
            {label}
          </span>
          <a
            className="icon-btn"
            href="https://github.com/Abhxym/redrob-ai"
            target="_blank"
            rel="noreferrer"
            aria-label="View source on GitHub"
          >
            <CodeXml size={16} />
          </a>
          <button
            type="button"
            className="icon-btn"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </header>
  );
}
