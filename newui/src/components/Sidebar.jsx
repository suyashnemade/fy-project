/* -----------------------------------------------------------------------
   Mode definitions — icon + label + id
   ----------------------------------------------------------------------- */
const MODES = [
  {
    id: 'search',
    label: 'Text to Image Search',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
    ),
  },
  {
    id: 'image',
    label: 'Image to Image Search',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect width="18" height="18" x="3" y="3" rx="2" />
        <circle cx="9" cy="9" r="2" />
        <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
      </svg>
    ),
  },
  {
    id: 'video',
    label: 'Video Frame Search',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5" />
        <rect x="2" y="6" width="14" height="12" rx="2" />
      </svg>
    ),
  },
];

/* -----------------------------------------------------------------------
   Component
   ----------------------------------------------------------------------- */
export default function Sidebar({ activeMode, onModeChange, history = [], onHistoryClick, isCollapsed, onOpenSettings }) {
  return (
    <aside className={`${isCollapsed ? 'w-20' : 'w-64'} transition-all duration-300 h-full bg-sidebar border-r-[0.5px] border-[#383838] flex flex-col pt-6 text-sidebar-foreground`} id="sidebar">
      {/* ---- Logo ---- */}
      <div className={`flex items-center gap-3 px-6 mb-8 select-none ${isCollapsed ? 'justify-center px-0' : ''}`}>
        <div className="w-10 h-10 shrink-0 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shadow-sm">
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </div>
        {!isCollapsed && (
          <div className="flex flex-col whitespace-nowrap overflow-hidden">
            <div className="text-sm font-semibold tracking-tight text-foreground">Image Search</div>
            <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Semantic Engine</div>
          </div>
        )}
      </div>

      {/* ---- Modes ---- */}
      <nav className={`flex flex-col px-4 mb-8 ${isCollapsed ? 'items-center px-2' : ''}`} aria-label="Search modes">
        {!isCollapsed && <div className="text-xs font-semibold text-sidebar-foreground/50 mb-2 px-2 uppercase tracking-wider">Modes</div>}
        <div className="flex flex-col gap-1 w-full">
          {MODES.map((mode) => {
            const isActive = activeMode === mode.id;
            return (
              <button
                key={mode.id}
                id={`mode-${mode.id}`}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${isCollapsed ? 'justify-center w-12 h-12 p-0 mx-auto' : ''} ${
                  isActive 
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground' 
                  : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground'
                }`}
                onClick={() => onModeChange(mode.id)}
                aria-current={isActive ? 'true' : undefined}
                title={isCollapsed ? mode.label : undefined}
              >
                <span className={isActive ? 'text-sidebar-accent-foreground' : 'text-sidebar-foreground/50'}>
                  {mode.icon}
                </span>
                {!isCollapsed && mode.label}
              </button>
            )
          })}
        </div>
      </nav>

      {/* ---- History ---- */}
      <div className={`flex flex-col flex-1 min-h-0 px-4 ${isCollapsed ? 'hidden' : ''}`}>
        <div className="flex items-center justify-between px-2 mb-2">
          <div className="text-xs font-semibold text-sidebar-foreground/50 uppercase tracking-wider">History</div>
        </div>
        <div className="flex-1 overflow-y-auto overflow-x-hidden pr-2">
          <div className="flex flex-col gap-1">
            {history.length === 0 ? (
              <div className="px-2 py-3 text-xs text-sidebar-foreground/40 text-center italic">No searches yet</div>
            ) : (
              history.map((item, i) => (
                <div
                  key={`${item}-${i}`}
                  className="flex items-center gap-2 group px-2 py-1.5 rounded-md text-sm text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground cursor-pointer truncate"
                  title={item}
                  onClick={() => onHistoryClick?.(item)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter') onHistoryClick?.(item); }}
                >
                  <svg className="w-3.5 h-3.5 shrink-0 text-sidebar-foreground/40 group-hover:text-sidebar-foreground/70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  <span className="truncate">{item}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ---- Settings ---- */}
      <div className={`p-4 border-t border-sidebar-border mt-auto ${isCollapsed ? 'flex justify-center' : ''}`}>
        <button 
          onClick={onOpenSettings}
          className={`flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent/50 rounded-md transition-colors ${isCollapsed ? 'w-12 h-12 p-0' : 'w-full'}`} id="settings-btn" title={isCollapsed ? "Settings" : undefined}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          {!isCollapsed && "Settings"}
        </button>
      </div>
    </aside>
  );
}
