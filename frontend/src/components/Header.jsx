export function Logo() {
  return (
    <svg width="26" height="18" viewBox="0 0 26 18" aria-hidden="true">
      <path d="M1 1h6l6 16H7z" fill="currentColor" />
      <path d="M11 1h6l6 16h-6z" fill="currentColor" />
    </svg>
  );
}

export default function Header({ health, offline, onHome }) {
  const warm = health?.warm_state;
  let status = 'wait';
  let label = 'Connecting…';
  if (offline || warm === 'error') {
    status = 'bad';
    label = warm === 'error' ? 'Pipeline failed' : 'API offline';
  } else if (warm === 'ready') {
    status = 'ok';
    label = `${(health.candidates_loaded ?? 0).toLocaleString()} profiles`;
  } else if (health) {
    label = 'Loading models…';
  }

  return (
    <header className="nav">
      <button type="button" className="nav-brand" onClick={onHome}>
        <Logo />
        <span>RedRob</span>
      </button>
      <span className="nav-rule" aria-hidden="true" />
      <nav className="nav-links">
        <a href="#how">How it works</a>
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API</a>
        <a href="https://github.com/Abhxym/redrob-ai" target="_blank" rel="noreferrer">GitHub</a>
      </nav>
      <span className={`nav-status status-${status}`} title={health?.error || undefined}>
        <span className="status-dot" />{label}
      </span>
    </header>
  );
}
