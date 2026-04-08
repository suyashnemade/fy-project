/* -----------------------------------------------------------------------
   ImageCard — single result tile with feedback buttons
   ----------------------------------------------------------------------- */
function ImageCard({ image, onImageClick, onFeedback, onPlayVideo, currentQuery }) {
  const hasImage = Boolean(image.src);

  return (
    <div className="relative flex flex-col group overflow-hidden bg-card border border-border rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-default" title={image.name}>
      <div
        className="relative aspect-square w-full bg-muted overflow-hidden flex items-center justify-center cursor-pointer group-hover:opacity-90 transition-opacity"
        onClick={() => hasImage && onImageClick?.(image)}
      >
        {hasImage ? (
          <img
            className="w-full h-full object-cover"
            src={image.src}
            alt={image.name}
            loading="lazy"
            draggable="false"
          />
        ) : (
          <div className="text-muted-foreground/30">
            <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <circle cx="9" cy="9" r="2" />
              <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
          </div>
        )}

        {image.score != null && (
          <span className="absolute top-2 right-2 bg-black/60 text-white text-[10px] font-mono px-1.5 py-0.5 rounded shadow-sm opacity-80 backdrop-blur-sm">
            {image.score.toFixed(3)}
          </span>
        )}
      </div>

      <div className="flex flex-col p-3 gap-2">
        <div className="text-sm font-medium text-foreground truncate">{image.name}</div>

        {/* Actions row: Play button (if video) + Feedback buttons */}
        <div className="flex w-full justify-between items-center gap-1">
          {image.isVideo && currentQuery ? (
             <button
              className="flex items-center gap-1 px-2 py-1 bg-secondary text-secondary-foreground text-xs font-medium rounded hover:opacity-80 transition-opacity"
              title="Play from this timestamp"
              onClick={(e) => {
                e.stopPropagation();
                onPlayVideo?.(image);
              }}
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Play
            </button>
          ) : <div />}

          {currentQuery && onFeedback && (
            <div className="flex gap-1">
              <button
                className="p-1 rounded bg-secondary text-secondary-foreground hover:bg-green-500/20 hover:text-green-600 transition-colors"
                title="Relevant"
                onClick={(e) => {
                  e.stopPropagation();
                  onFeedback(image, 'relevant');
                }}
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 19V5" />
                  <path d="M5 12l7-7 7 7" />
                </svg>
              </button>
              <button
                className="p-1 rounded bg-secondary text-secondary-foreground hover:bg-destructive hover:text-destructive-foreground transition-colors"
                title="Not relevant"
                onClick={(e) => {
                  e.stopPropagation();
                  onFeedback(image, 'not_relevant');
                }}
              >
                <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 5v14" />
                  <path d="M19 12l-7 7-7-7" />
                </svg>
              </button>
            </div>
          )}
        </div>
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
  onPlayVideo,
  currentQuery,
}) {
  /* Loading state */
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 h-full min-h-[400px]">
        <div className="flex flex-col items-center justify-center max-w-sm text-center text-muted-foreground animate-pulse">
          <div className="w-8 h-8 mb-4 rounded-full border-4 border-muted border-t-primary animate-spin" />
          <span className="text-lg font-semibold text-foreground mb-1">Searching…</span>
          <span className="text-sm">
            Finding the best matches for your query.
          </span>
        </div>
      </div>
    );
  }

  /* Not loaded warning */
  if (!directoryLoaded && images.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 h-full min-h-[400px]">
        <div className="flex flex-col items-center justify-center max-w-sm text-center text-muted-foreground p-8 rounded-lg border border-dashed border-border bg-muted/30">
          <div className="mb-4 text-amber-500 opacity-80">
            <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
            </svg>
          </div>
          <span className="text-lg font-semibold text-foreground mb-1">No directory loaded</span>
          <span className="text-sm">
            Click "Load Directory" or drag & drop a folder to get started.
          </span>
        </div>
      </div>
    );
  }

  /* Empty results (directory loaded but no search results yet) */
  if (images.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 h-full min-h-[400px]">
        <div className="flex flex-col items-center justify-center max-w-sm text-center text-muted-foreground">
          <div className="mb-4 opacity-50">
            <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <circle cx="9" cy="9" r="2" />
              <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
            </svg>
          </div>
          <span className="text-lg font-semibold text-foreground mb-1">Ready to search</span>
          <span className="text-sm">
            Type a query and press Enter to see search results.
          </span>
        </div>
      </div>
    );
  }

  /* Results grid */
  return (
    <div className="flex-1 overflow-y-auto p-6" style={{ height: 'calc(100vh - 120px)' }}>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-6">
        {images.map((image, i) => (
          <ImageCard
            key={image.id ?? i}
            image={image}
            onImageClick={onImageClick}
            onFeedback={onFeedback}
            onPlayVideo={onPlayVideo}
            currentQuery={currentQuery}
          />
        ))}
      </div>
    </div>
  );
}
