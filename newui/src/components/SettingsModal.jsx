import { useState } from 'react';

export default function SettingsModal({ onClose, currentTheme, onThemeChange, indexInfo, onDeleteIndex }) {
  const [isDeleting, setIsDeleting] = useState(false);
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
          
          
          {/* System & Model Information */}
          <div className="pt-4 border-t border-border space-y-3">
            <h3 className="text-sm font-semibold text-foreground">System Engine</h3>
            
            <div className="bg-muted p-3 rounded-md text-xs font-mono space-y-2 text-muted-foreground">
              <div className="flex justify-between">
                <span>Model Architecture</span>
                <span className="text-foreground">clip-ViT-B-32</span>
              </div>
              <div className="flex justify-between">
                <span>Total Images Indexed</span>
                <span className="text-foreground">{indexInfo?.imageCount || 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Vector DB Storage</span>
                <span className="text-foreground">{indexInfo?.sizeBytes ? (indexInfo.sizeBytes / 1024 / 1024).toFixed(2) + ' MB' : '0 MB'}</span>
              </div>
            </div>
            
            <button 
              onClick={async () => {
                if (window.confirm("Are you sure you want to permanently delete all FAISS vector indexes and metadata? This cannot be undone.")) {
                  setIsDeleting(true);
                  await onDeleteIndex?.();
                  setIsDeleting(false);
                  onClose();
                }
              }}
              disabled={isDeleting || !indexInfo?.imageCount}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 mt-4 bg-destructive/10 text-destructive border border-destructive/20 rounded-md hover:bg-destructive/20 transition-colors disabled:opacity-50 text-sm font-medium"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
              </svg>
              {isDeleting ? "Deleting..." : "Clear Index Data"}
            </button>
          </div>
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
