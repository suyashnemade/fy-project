import '../styles/sidebar.css';

/* -----------------------------------------------------------------------
   Mode definitions — icon + label + id
   ----------------------------------------------------------------------- */
const MODES = [
  {
    id: 'search',
    label: 'Text Search',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    ),
  },
  {
    id: 'image',
    label: 'Image Search',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect width="18" height="18" x="3" y="3" rx="2" />
        <circle cx="9" cy="9" r="2" />
        <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
      </svg>
    ),
  },
  {
    id: 'video',
    label: 'Video Search',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5" />
        <rect x="2" y="6" width="14" height="12" rx="2" />
      </svg>
    ),
  },
//  {
//     id: 'qa',
//     label: 'Q & A',
//     icon: (
//       <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
//         <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
//         <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
//         <path d="M12 17h.01" />
//       </svg>
//     ),
//   }, 
];

/* -----------------------------------------------------------------------
   Component
   ----------------------------------------------------------------------- */
export default function Sidebar({ activeMode, onModeChange, history = [], onHistoryClick }) {
  return (
    <aside className="sidebar" id="sidebar">
      {/* ---- Logo ---- */}
      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </div>
        <div>
          <div className="sidebar__logo-title">Image Search</div>
          <div className="sidebar__logo-subtitle">Semantic Engine</div>
        </div>
      </div>

      {/* ---- Modes ---- */}
      <nav className="sidebar__section" aria-label="Search modes">
        <div className="sidebar__section-label">Modes</div>
        <div className="sidebar__modes">
          {MODES.map((mode) => (
            <button
              key={mode.id}
              id={`mode-${mode.id}`}
              className={`sidebar__mode-btn${activeMode === mode.id ? ' sidebar__mode-btn--active' : ''}`}
              onClick={() => onModeChange(mode.id)}
              aria-current={activeMode === mode.id ? 'true' : undefined}
            >
              <span className="sidebar__mode-icon">{mode.icon}</span>
              {mode.label}
            </button>
          ))}
        </div>
      </nav>

      {/* ---- History ---- */}
      <div className="sidebar__history-section">
        <div className="sidebar__history-header">
          <div className="sidebar__section-label">History</div>
        </div>
        <div className="sidebar__history-scroll">
          <div className="sidebar__history-list">
            {history.length === 0 ? (
              <div className="sidebar__history-empty">No searches yet</div>
            ) : (
              history.map((item, i) => (
                <div
                  key={`${item}-${i}`}
                  className="sidebar__history-item"
                  title={item}
                  onClick={() => onHistoryClick?.(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter') onHistoryClick?.(item); }}
                >
                  <svg className="sidebar__history-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  {item}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ---- Settings ---- */}
      <div className="sidebar__bottom">
        <button className="sidebar__settings-btn" id="settings-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          Settings
        </button>
      </div>
    </aside>
  );
}
