export default function SettingsModal({ onClose, currentTheme, onThemeChange }) {
  // Temporary hardcoded list as we prepare for multiple themes
  const availableThemes = [
    { id: 'mono', label: 'Mono Theme' },
    { id: 'light', label: 'Light Theme' },
    { id: 'dark', label: 'Dark Theme' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={onClose}>
      <div 
        className="w-full max-w-sm bg-card text-card-foreground rounded-xl shadow-2xl border border-border p-6" 
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Settings</h2>
          <button 
            onClick={onClose} 
            className="p-1 hover:bg-muted text-muted-foreground rounded-md transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Active Theme</label>
            <select 
              value={currentTheme}
              onChange={(e) => onThemeChange(e.target.value)}
              className="w-full h-10 px-3 rounded-md border border-input bg-background font-medium text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {availableThemes.map(t => (
                <option key={t.id} value={t.id}>{t.label}</option>
              ))}
            </select>
            <p className="text-xs text-muted-foreground mt-1">Select the semantic engine interface aesthetic.</p>
          </div>
          
          {/* Future settings can go here */}
        </div>

        <div className="mt-8 flex justify-end">
          <button 
            onClick={onClose} 
            className="px-4 py-2 bg-primary text-primary-foreground font-medium rounded-md hover:opacity-90 transition-opacity text-sm"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
