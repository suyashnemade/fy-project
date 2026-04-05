import { useEffect } from 'react';
import '../styles/lightbox.css';

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
    <div className="lightbox" onClick={onClose}>
      <div className="lightbox__inner" onClick={(e) => e.stopPropagation()}>
        {/* Close button */}
        <button className="lightbox__close" onClick={onClose} aria-label="Close">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6 6 18" />
            <path d="m6 6 12 12" />
          </svg>
        </button>

        {/* Image */}
        <img
          className="lightbox__img"
          src={image.src}
          alt={image.name}
          draggable="false"
        />

        {/* Info bar */}
        <div className="lightbox__info">
          <span className="lightbox__name">{image.name}</span>
          {image.score != null && (
            <span className="lightbox__score">Score: {image.score.toFixed(4)}</span>
          )}
        </div>
      </div>
    </div>
  );
}
