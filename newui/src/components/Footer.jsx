/**
 * Footer — slim status bar showing image count, processing time, index size.
 */
export default function Footer({
  imageCount = 0,
  processingTime = '—',
  indexSize = '—',
}) {
  return (
    <footer className="flex items-center gap-6 px-6 py-2 bg-card border-t border-border text-xs text-muted-foreground select-none" id="footer-bar">
      {/* Image count */}
      <div className="flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect width="18" height="18" x="3" y="3" rx="2" />
          <circle cx="9" cy="9" r="2" />
          <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
        </svg>
        <span className="font-medium mr-1">Images:</span>
        <span className="font-mono text-foreground">{imageCount}</span>
      </div>

      {/* Processing time */}
      <div className="flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        <span className="font-medium mr-1">Time:</span>
        <span className="font-mono text-foreground">{processingTime}</span>
      </div>

      {/* Index size */}
      <div className="flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M3 5v14a9 3 0 0 0 18 0V5" />
          <path d="M3 12a9 3 0 0 0 18 0" />
        </svg>
        <span className="font-medium mr-1">Index:</span>
        <span className="font-mono text-foreground">{indexSize}</span>
      </div>
    </footer>
  );
}
