import { useEffect } from 'react';

/**
 * Lightbox — full-screen modal to view an image in detail.
 *
 * Props:
 *   image   — { name, src, score } or null to hide
 *   onClose — callback to close the modal
 */
export default function Lightbox({ image, onClose }) {
  /* Close on Escape key */
  useEffect(() => {
    if (!image) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [image, onClose]);

  if (!image) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200" onClick={onClose}>
      <div className="relative flex flex-col max-w-7xl max-h-[90vh] bg-card rounded-lg shadow-2xl overflow-hidden border border-border" onClick={(e) => e.stopPropagation()}>
        {/* Close button */}
        <button className="absolute top-4 right-4 p-2 bg-black/50 hover:bg-black/80 text-white rounded-full transition-colors z-10" onClick={onClose} aria-label="Close">
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
          </svg>
        </button>

        {/* Image */}
        <div className="flex-1 overflow-hidden bg-muted flex items-center justify-center p-2">
          <img
            className="max-w-full max-h-[calc(90vh-80px)] object-contain rounded-md"
            src={image.src}
            alt={image.name}
            draggable="false"
          />
        </div>

        {/* Info bar */}
        <div className="flex items-center justify-between p-4 bg-card border-t border-border mt-auto">
          <span className="font-medium text-foreground truncate mr-4">{image.name}</span>
          {image.score != null && (
            <span className="text-sm font-mono text-muted-foreground bg-muted px-2 py-1 rounded-md">Score: {image.score.toFixed(4)}</span>
          )}
        </div>
      </div>
    </div>
  );
}
