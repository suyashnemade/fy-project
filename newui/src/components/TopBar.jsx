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
  activeMode,
  onToggleSidebar,
  children,
}) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') onSearch?.();
  };

  return (
    <header className="flex flex-col gap-4 p-6 border-b border-border bg-card text-card-foreground relative" id="topbar">
      {/* Theme Toggle in top absolute corner */}
      <button
        id="theme-toggle"
        className="absolute top-4 right-4 p-2 rounded-md hover:bg-muted text-muted-foreground transition-colors"
        onClick={onToggleTheme}
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {isDark ? (
          /* Sun icon */
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2" /><path d="M12 20v2" />
            <path d="m4.93 4.93 1.41 1.41" /><path d="m17.66 17.66 1.41 1.41" />
            <path d="M2 12h2" /><path d="M20 12h2" />
            <path d="m6.34 17.66-1.41 1.41" /><path d="m19.07 4.93-1.41 1.41" />
          </svg>
        ) : (
          /* Moon icon */
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
          </svg>
        )}
      </button>

      <div className="flex gap-4 items-start w-full">
        {/* Hamburger Menu */}
        <button 
          onClick={onToggleSidebar}
          className="p-2 rounded-md hover:bg-muted text-muted-foreground transition-colors self-start mt-1 mr-4"
          aria-label="Toggle Sidebar"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>

        {/* Row 1 — Search */}
        {activeMode !== 'image' && (
          <div className="flex justify-center flex-1">
            <div className="relative flex w-full max-w-2xl items-center">
              <svg className="absolute left-4 w-5 h-5 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                id="search-input"
                className="w-full h-12 pl-12 pr-24 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring shadow-sm transition-all"
                type="text"
                placeholder="Type your query…"
                value={query}
                onChange={(e) => onQueryChange(e.target.value)}
                onKeyDown={handleKeyDown}
                autoComplete="off"
                spellCheck="false"
              />
              <button 
                className="absolute right-1 text-sm bg-primary text-primary-foreground h-10 px-6 rounded-md hover:opacity-90 font-medium transition-colors" 
                onClick={onSearch}
              >
                Search
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Row 2 — Actions */}
      <div className="flex justify-center flex-wrap items-center gap-4 text-sm mt-2 w-full">
        {activeMode === 'video' ? (
          <div className="flex flex-col items-center w-full max-w-3xl justify-center">
            {children}
          </div>
        ) : (
          <>
            <button 
              id="load-directory-btn" 
              className="flex items-center gap-2 bg-secondary text-secondary-foreground px-4 h-10 rounded-md hover:opacity-80 transition-colors shadow-sm whitespace-nowrap" 
              onClick={onLoadDirectory}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
              </svg>
              Load Directory
            </button>

            {activeMode === 'image' && (
              <div className="flex items-center">
                {children}
              </div>
            )}

            {directoryPath && (
              <span className="flex items-center gap-2 px-3 py-1.5 bg-muted text-muted-foreground rounded-md border border-border text-xs" title={directoryPath}>
                <span className="font-semibold text-foreground">Location:</span>
                <span className="truncate max-w-[200px]">{directoryPath}</span>
              </span>
            )}

            {resultCount > 0 && query && (
              <span className="text-muted-foreground text-sm">
                Found <strong className="text-foreground font-semibold">{resultCount}</strong> results for &ldquo;{query}&rdquo;
              </span>
            )}
          </>
        )}
      </div>
    </header>
  );
}
