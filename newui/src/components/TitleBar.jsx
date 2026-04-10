import { getCurrentWindow } from '@tauri-apps/api/window';

export default function TitleBar() {
  const appWindow = getCurrentWindow();

  return (
    <div 
      className="h-10 w-full flex justify-between items-center select-none bg-background border-b border-border text-foreground"
    >
      {/* App Logo / Title area - make sure drag-region is applied so you can drag here */}
      <div data-tauri-drag-region="true" className="w-full h-full pl-4 flex items-center text-sm font-semibold text-muted-foreground hover:text-foreground transition-colors cursor-default">
        <span data-tauri-drag-region="true" className="seekr-brand">Seekr</span>
      </div>

      {/* Window Controls (Minimize, Maximize, Close) */}
      <div className="flex h-full">
        {/* Minimize */}
        <button 
          onClick={() => appWindow.minimize()}
          className="px-4 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center"
        >
          <svg width="12" height="12" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="1" y1="5" x2="9" y2="5" stroke="currentColor" strokeWidth="1" />
          </svg>
        </button>

        {/* Maximize / Restore */}
        <button 
          onClick={() => appWindow.toggleMaximize()}
          className="px-4 hover:bg-muted text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center"
        >
          <svg width="12" height="12" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="1.5" y="1.5" width="7" height="7" stroke="currentColor" strokeWidth="1" />
          </svg>
        </button>

        {/* Close (Red hover) */}
        <button 
          onClick={() => appWindow.close()}
          className="px-4 hover:bg-destructive hover:text-destructive-foreground text-muted-foreground transition-colors flex items-center justify-center"
        >
          <svg width="12" height="12" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M2.5 2.5L7.5 7.5M7.5 2.5L2.5 7.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}
