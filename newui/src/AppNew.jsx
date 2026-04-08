import { useState, useEffect, useRef } from 'react';
import './styles/theme.css';

import Layout from './layout/Layout';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ImageGrid from './components/ImageGrid';
import Footer from './components/Footer';
import Lightbox from './components/Lightbox';

import {
  healthCheck,
  getIndexStatus,
  searchByText,
  searchByImage,
  searchVideo,
  indexDirectory,
  getImageUrl,
  getVideoUrl,
  addFeedback,
} from './api';

/* -----------------------------------------------------------------------
   Helper — format bytes to human-readable string
   ----------------------------------------------------------------------- */
function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

/* -----------------------------------------------------------------------
   AppNew — root component for the new UI
   ----------------------------------------------------------------------- */
export default function AppNew() {
  /* ---- Core state ---- */
  const [activeMode, setActiveMode] = useState('search');
  const [query, setQuery] = useState('');
  const [images, setImages] = useState([]);

  /* ---- Directory / index state ---- */
  const [directoryPath, setDirectoryPath] = useState('');
  const [directoryLoaded, setDirectoryLoaded] = useState(false);

  /* ---- Loading / error / status state ---- */
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [processingTime, setProcessingTime] = useState('—');
  const [indexInfo, setIndexInfo] = useState({ imageCount: 0, sizeBytes: 0 });
  const [backendReady, setBackendReady] = useState(false);

  /* ---- Search history ---- */
  const [history, setHistory] = useState([]);

  /* ---- Drag-and-drop state ---- */
  const [isDragging, setIsDragging] = useState(false);

  /* ---- Image search state ---- */
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  /* ---- Video search state ---- */
  const [videoPath, setVideoPath] = useState('');
  const [videoFps, setVideoFps] = useState('1.0');
  const [videoResults, setVideoResults] = useState([]);
  const videoInputRef = useRef(null);
  const [playingVideoUrl, setPlayingVideoUrl] = useState(null);

  /* ---- Lightbox state ---- */
  const [lightboxImage, setLightboxImage] = useState(null);

  /* ---- Theme ---- */
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains('dark')
  );

  /* ---- Refs ---- */
  const dirInputRef = useRef(null);
  const imageInputRef = useRef(null);

  /* ---- Theme sync ---- */
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
  }, [isDark]);

  /* ---- Auto-clear success messages after 4 seconds ---- */
  useEffect(() => {
    if (successMsg) {
      const timer = setTimeout(() => setSuccessMsg(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [successMsg]);

  /* ---- On mount: check backend health + index status ---- */
  useEffect(() => {
    async function init() {
      const healthResult = await healthCheck();
      if (healthResult.error) {
        setError('Backend is not running. Start it with: uvicorn newuiapi.main:app --reload');
        return;
      }

      setBackendReady(true);

      if (healthResult.data.index_ready) {
        setDirectoryLoaded(true);
        setDirectoryPath('Previously indexed');
      }

      const statusResult = await getIndexStatus();
      if (statusResult.data) {
        setIndexInfo({
          imageCount: statusResult.data.image_count,
          sizeBytes: statusResult.data.index_size_bytes,
        });
        if (statusResult.data.image_count > 0) {
          setDirectoryLoaded(true);
        }
      }
    }

    init();
  }, []);

  /* ---- Clean up image preview URL when file changes ---- */
  useEffect(() => {
    if (!imageFile) {
      setImagePreview(null);
      return;
    }
    const url = URL.createObjectURL(imageFile);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [imageFile]);

  /* ---- Shared: map API search results to grid format ---- */
  const mapResults = (results) =>
    results.map((r) => ({
      id: r.rank,
      name: r.filename,
      src: getImageUrl(r.image_path),
      score: r.score,
      imagePath: r.image_path,   // keep for feedback
    }));

  /* ---- Text Search handler ---- */
  const handleSearch = async () => {
    if (activeMode === 'image') {
      handleImageSearch();
      return;
    }
    if (activeMode === 'video') {
      handleVideoSearch();
      return;
    }

    const trimmed = query.trim();
    if (!trimmed) return;

    if (!directoryLoaded) {
      setError('No directory loaded yet. Please load a directory first.');
      return;
    }

    setError(null);
    setLoading(true);
    setImages([]);

    const result = await searchByText(trimmed);

    setLoading(false);

    if (result.error) {
      setError(result.error);
      return;
    }

    setImages(mapResults(result.data.results));
    setProcessingTime(`${result.data.took_ms.toFixed(0)}ms`);

    setHistory((prev) => {
      const filtered = prev.filter((h) => h !== trimmed);
      return [trimmed, ...filtered].slice(0, 10);
    });
  };

  /* ---- Image Search handler ---- */
  const handleImageSearch = async () => {
    if (!imageFile) {
      setError('Please select an image to search with.');
      return;
    }
    if (!directoryLoaded) {
      setError('No directory loaded yet. Please load a directory first.');
      return;
    }

    setError(null);
    setLoading(true);
    setImages([]);

    const result = await searchByImage(imageFile);

    setLoading(false);

    if (result.error) {
      setError(result.error);
      return;
    }

    setImages(mapResults(result.data.results));
    setProcessingTime(`${result.data.took_ms.toFixed(0)}ms`);
  };

  /* ---- Video Search handler ---- */
  const handleVideoSearch = async () => {
    const trimmedQuery = query.trim();
    const trimmedPath = videoPath.trim().replace(/^["']|["']$/g, '');

    if (!trimmedPath) {
      setError('Please enter the video file path.');
      return;
    }
    if (!trimmedQuery) {
      setError('Please enter a text query to search for in the video.');
      return;
    }

    setError(null);
    setLoading(true);
    setImages([]);
    setVideoResults([]);

    const result = await searchVideo({
      videoPath: trimmedPath,
      query: trimmedQuery,
      fps: parseFloat(videoFps) || 1.0,
    });

    setLoading(false);

    if (result.error) {
      setError(result.error);
      return;
    }

    // Video results return base64 frames — map them for the grid
    const mapped = result.data.results.map((r, i) => ({
      id: i + 1,
      name: `Frame @ ${r.formatted_time}`,
      src: `data:image/jpeg;base64,${r.frame_base64}`,
      score: r.score,
      isVideo: true,
      videoPath: trimmedPath,
      timestamp: r.timestamp,
    }));

    setImages(mapped);
    setVideoResults(result.data.results);
  };

  /* ---- History click handler ---- */
  const handleHistoryClick = (historyQuery) => {
    setQuery(historyQuery);
    setTimeout(async () => {
      if (!directoryLoaded) {
        setError('No directory loaded yet. Please load a directory first.');
        return;
      }

      setError(null);
      setLoading(true);
      setImages([]);

      const result = await searchByText(historyQuery);
      setLoading(false);

      if (result.error) {
        setError(result.error);
        return;
      }

      setImages(mapResults(result.data.results));
      setProcessingTime(`${result.data.took_ms.toFixed(0)}ms`);
    }, 0);
  };

  /* ---- Feedback handler ---- */
  const handleFeedback = async (image, feedbackType) => {
    const result = await addFeedback({
      query: query.trim(),
      imagePath: image.imagePath || '',
      feedback: feedbackType,
      rank: image.id,
      score: image.score,
    });

    if (result.error) {
      setError(`Feedback failed: ${result.error}`);
    } else {
      setSuccessMsg(`Feedback recorded: ${feedbackType === 'relevant' ? 'Positive' : 'Negative'}`);
    }
  };

  /* ---- Lightbox handlers ---- */
  const handleImageClick = (image) => {
    setLightboxImage(image);
  };

  const handleCloseLightbox = () => {
    setLightboxImage(null);
  };

  /* ---- Index a directory (shared logic) ---- */
  const doIndexDirectory = async (dirPath) => {
    if (!dirPath) return;

    setError(null);
    setIndexing(true);
    setSuccessMsg(null);

    const result = await indexDirectory(dirPath);

    setIndexing(false);

    if (result.error) {
      setError(`Indexing failed: ${result.error}`);
      return;
    }

    setDirectoryPath(dirPath);
    setDirectoryLoaded(true);
    setSuccessMsg(
      `Indexed ${result.data.successful} images (${result.data.total_indexed} total)`
    );

    const statusResult = await getIndexStatus();
    if (statusResult.data) {
      setIndexInfo({
        imageCount: statusResult.data.image_count,
        sizeBytes: statusResult.data.index_size_bytes,
      });
    }
  };

  /* ---- Load Directory button handler ---- */
  const handleLoadDirectory = () => {
    if (dirInputRef.current) {
      dirInputRef.current.click();
    }
  };

  /* ---- Handle folder selection from <input webkitdirectory> ---- */
  const handleFolderSelect = (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const firstPath = files[0].webkitRelativePath || '';
    const folderName = firstPath.split('/')[0] || 'selected folder';

    const absolutePath = window.prompt(
      `You selected "${folderName}" (${files.length} files).\n\n` +
      `The backend needs the full absolute path to this folder.\n` +
      `Please paste the full path below:`,
      `D:\\${folderName}`
    );

    e.target.value = '';

    if (absolutePath && absolutePath.trim()) {
      doIndexDirectory(absolutePath.trim());
    }
  };

  /* ---- Image file selection for image search ---- */
  const handleImageFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
    }
  };

  /* ---- Drag & Drop handlers ---- */
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const items = e.dataTransfer?.items;
    let folderName = 'your folder';

    if (items && items.length > 0) {
      const entry = items[0].webkitGetAsEntry?.();
      if (entry && entry.isDirectory) {
        folderName = entry.name;
      }
    }

    const absolutePath = window.prompt(
      `You dropped "${folderName}".\n\n` +
      `The backend needs the full absolute path to index it.\n` +
      `Please paste the full path below:`,
      `D:\\${folderName}`
    );

    if (absolutePath && absolutePath.trim()) {
      doIndexDirectory(absolutePath.trim());
    }
  };

  /* ---- Render ---- */
  return (
    <Layout sidebar={
      <Sidebar
        activeMode={activeMode}
        onModeChange={setActiveMode}
        history={history}
        onHistoryClick={handleHistoryClick}
      />
    }>
      {/* Hidden inputs */}
      <input
        ref={dirInputRef}
        type="file"
        webkitdirectory=""
        directory=""
        multiple
        style={{ display: 'none' }}
        onChange={handleFolderSelect}
      />
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleImageFileSelect}
      />
      <input
        ref={videoInputRef}
        type="file"
        accept="video/*"
        style={{ display: 'none' }}
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            const absolutePath = window.prompt(
              `You selected "${file.name}".\n\nSecurity Sandbox: The browser cannot read your disk automatically.\nPlease paste the full absolute path to this video file below (e.g. D:\\videos\\${file.name}):`,
              ''
            );
            e.target.value = '';
            if (absolutePath && absolutePath.trim()) {
              setVideoPath(absolutePath.trim().replace(/^["']|["']$/g, ''));
            }
          }
        }}
      />

      <TopBar
        query={query}
        onQueryChange={setQuery}
        onSearch={handleSearch}
        onLoadDirectory={handleLoadDirectory}
        directoryPath={directoryPath}
        resultCount={images.length}
        isDark={isDark}
        onToggleTheme={() => setIsDark((d) => !d)}
      />

      {/* ---- Mode-specific input areas ---- */}
      {activeMode === 'image' && (
        <div className="mode-panel">
          <div className="mode-panel__row">
            <button
              className="mode-panel__btn"
              onClick={() => imageInputRef.current?.click()}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}>
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              {imageFile ? 'Change Image' : 'Select Image'}
            </button>

            {imagePreview && (
              <div className="mode-panel__preview">
                <img src={imagePreview} alt="Query preview" />
                <span className="mode-panel__filename">{imageFile?.name}</span>
                <button
                  className="mode-panel__clear"
                  onClick={() => {
                    setImageFile(null);
                    if (imageInputRef.current) imageInputRef.current.value = '';
                  }}
                  title="Clear"
                >✕</button>
              </div>
            )}

            {imageFile && (
              <button className="mode-panel__search-btn" onClick={handleImageSearch}>
                Search Similar
              </button>
            )}
          </div>
        </div>
      )}

      {activeMode === 'video' && (
        <div className="mode-panel">
          <div className="mode-panel__row">
            <button
               className="mode-panel__btn"
               onClick={() => videoInputRef.current?.click()}
               style={{ flexShrink: 0 }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}>
                 <polygon points="23 7 16 12 23 17 23 7" />
                 <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
              {videoPath ? 'Change Video' : 'Select Video'}
            </button>
            <input
              className="mode-panel__input"
              type="text"
              placeholder="Paste absolute path (or click Select Video)"
              value={videoPath}
              onChange={(e) => setVideoPath(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleVideoSearch()}
            />
            <select
               value={videoFps}
               onChange={e => setVideoFps(e.target.value)}
               className="mode-panel__select"
               style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--background)', color: 'var(--foreground)' }}
               title="Frame Extraction Rate"
            >
               <option value="0.1">1 frame per 10s</option>
               <option value="0.2">1 frame per 5s</option>
               <option value="0.5">1 frame per 2s</option>
               <option value="1.0">1 frame per 1s</option>
               <option value="2.0">2 frames per 1s</option>
               <option value="5.0">5 frames per 1s</option>
            </select>
            <button className="mode-panel__search-btn" onClick={handleVideoSearch}>
              Search Frames
            </button>
          </div>
          <div className="mode-panel__hint">
            {videoPath ? `Selected: ${videoPath}` : 'Select a video and enter a text query above.'}
          </div>
        </div>
      )}

      {/* Status messages */}
      {error && (
        <div className="status-banner status-banner--error">
          <span>⚠ {error}</span>
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}
      {successMsg && (
        <div className="status-banner status-banner--success">
          <span>✓ {successMsg}</span>
        </div>
      )}
      {indexing && (
        <div className="status-banner status-banner--info">
          <span className="spinner-inline" /> Indexing images… this may take a moment.
        </div>
      )}

      {/* Main content area with drag-drop support */}
      <div
        className={`layout__content ${isDragging ? 'layout__content--dragging' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragging && (
          <div className="drop-overlay">
            <div className="drop-overlay__box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
                <path d="M12 10v6" />
                <path d="m9 13 3-3 3 3" />
              </svg>
              <span>Drop folder here to index</span>
            </div>
          </div>
        )}

        <ImageGrid
          images={images}
          loading={loading}
          directoryLoaded={directoryLoaded}
          onImageClick={handleImageClick}
          onFeedback={handleFeedback}
          onPlayVideo={image => setPlayingVideoUrl(getVideoUrl(image.videoPath, image.timestamp))}
          currentQuery={query.trim()}
        />
      </div>

      <Footer
        imageCount={indexInfo.imageCount}
        processingTime={processingTime}
        indexSize={formatBytes(indexInfo.sizeBytes)}
      />

      {/* Video Player Modal */}
      {playingVideoUrl && (
        <div className="lightbox" onClick={() => setPlayingVideoUrl(null)}>
          <div className="lightbox__content" onClick={e => e.stopPropagation()}>
            <video controls autoPlay src={playingVideoUrl} style={{ maxWidth: '100%', maxHeight: '80vh', backgroundColor: 'black' }} />
            <button className="lightbox__close" onClick={() => setPlayingVideoUrl(null)}>✕</button>
          </div>
        </div>
      )}

      {/* Lightbox modal */}
      <Lightbox image={lightboxImage} onClose={handleCloseLightbox} />
    </Layout>
  );
}
