import '../styles/imagegrid.css';

/* -----------------------------------------------------------------------
   ImageCard — single result tile with feedback buttons
   ----------------------------------------------------------------------- */
function ImageCard({ image, onImageClick, onFeedback, currentQuery }) {
  const hasImage = Boolean(image.src);

  return (
    <div className="image-card" title={image.name}>
      <div
        className="image-card__visual"
        onClick={() => hasImage && onImageClick?.(image)}
      >
        {hasImage ? (
          <img
            className="image-card__img"
            src={image.src}
            alt={image.name}
            loading="lazy"
            draggable="false"
          />
        ) : (
          <div className="image-card__placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <circle cx="9" cy="9" r="2" />
              <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
          </div>
        )}

        {image.score != null && (
          <span className="image-card__score">
            {image.score.toFixed(3)}
          </span>
        )}
      </div>

      <div className="image-card__info">
        <div className="image-card__name">{image.name}</div>

        {/* Feedback buttons — only show when we have a query context */}
        {currentQuery && onFeedback && (
          <div className="image-card__actions">
            <button
              className="image-card__action-btn image-card__action-btn--up"
              title="Relevant"
              onClick={(e) => {
                e.stopPropagation();
                onFeedback(image, 'relevant');
              }}
            >
              👍
            </button>
            <button
              className="image-card__action-btn image-card__action-btn--down"
              title="Not relevant"
              onClick={(e) => {
                e.stopPropagation();
                onFeedback(image, 'not_relevant');
              }}
            >
              👎
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

/* -----------------------------------------------------------------------
   ImageGrid — responsive grid of cards, loading state, or empty state
   ----------------------------------------------------------------------- */
export default function ImageGrid({
  images = [],
  loading = false,
  directoryLoaded = false,
  onImageClick,
  onFeedback,
  currentQuery,
}) {
  /* Loading state */
  if (loading) {
    return (
      <div className="image-grid">
        <div className="image-grid__empty">
          <div className="image-grid__spinner" />
          <span className="image-grid__empty-title">Searching…</span>
          <span className="image-grid__empty-desc">
            Finding the best matches for your query.
          </span>
        </div>
      </div>
    );
  }

  /* Not loaded warning */
  if (!directoryLoaded && images.length === 0) {
    return (
      <div className="image-grid">
        <div className="image-grid__empty">
          <div className="image-grid__empty-icon image-grid__empty-icon--warn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
            </svg>
          </div>
          <span className="image-grid__empty-title">No directory loaded</span>
          <span className="image-grid__empty-desc">
            Click "Load Directory" or drag & drop a folder to get started.
          </span>
        </div>
      </div>
    );
  }

  /* Empty results (directory loaded but no search results yet) */
  if (images.length === 0) {
    return (
      <div className="image-grid">
        <div className="image-grid__empty">
          <div className="image-grid__empty-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <circle cx="9" cy="9" r="2" />
              <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
          </div>
          <span className="image-grid__empty-title">Ready to search</span>
          <span className="image-grid__empty-desc">
            Type a query and press Enter to see search results.
          </span>
        </div>
      </div>
    );
  }

  /* Results grid */
  return (
    <div className="image-grid">
      <div className="image-grid__grid">
        {images.map((image, i) => (
          <ImageCard
            key={image.id ?? i}
            image={image}
            onImageClick={onImageClick}
            onFeedback={onFeedback}
            currentQuery={currentQuery}
          />
        ))}
      </div>
    </div>
  );
}
