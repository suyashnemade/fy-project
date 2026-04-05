import '../styles/topbar.css';

/**
 * TopBar — search input, load-directory action, directory badge, result count, theme toggle.
 *
 * All state is owned by the parent; this is a pure presentational component.
 */
export default function TopBar({
  query,
  onQueryChange,
  onSearch,
  onLoadDirectory,
  directoryPath,
  resultCount,
  isDark,
  onToggleTheme,
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') onSearch?.();
  };

  return (
    <header className="topbar" id="topbar">
      {/* Theme Toggle in top absolute corner */}
      <button
        id="theme-toggle"
        className="topbar__theme-btn"
        onClick={onToggleTheme}
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {isDark ? (
          /* Sun icon */
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2" /><path d="M12 20v2" />
            <path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" />
            <path d="M2 12h2" /><path d="M20 12h2" />
            <path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
          </svg>
        ) : (
          /* Moon icon */
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
          </svg>
        )}
      </button>

      {/* Row 1 — Search */}
      <div className="topbar__row-search">
        <div className="topbar__search-box">
          <svg className="topbar__search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            id="search-input"
            className="topbar__search-input"
            type="text"
            placeholder="Type your query…"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={handleKeyDown}
            autoComplete="off"
            spellCheck="false"
          />
          <button className="topbar__search-btn" onClick={onSearch}>Search</button>
        </div>
      </div>

      {/* Row 2 — Actions */}
      <div className="topbar__row-actions">
        <button id="load-directory-btn" className="topbar__load-btn" onClick={onLoadDirectory}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
          </svg>
          Load Directory
        </button>

        {directoryPath && (
          <span className="topbar__dir-badge" title={directoryPath}>
            <span className="topbar__dir-badge-label">Location:</span>
            <span className="topbar__dir-badge-path">{directoryPath}</span>
          </span>
        )}

        {resultCount > 0 && query && (
          <span className="topbar__result-status">
            Found <strong>{resultCount}</strong> results for &ldquo;{query}&rdquo;
          </span>
        )}
      </div>
    </header>
  );
}
