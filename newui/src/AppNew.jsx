import { useState, useEffect, useRef } from 'react';

import Layout from './layout/Layout';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ImageGrid from './components/ImageGrid';
import Footer from './components/Footer';
import Lightbox from './components/Lightbox';
import SettingsModal from './components/SettingsModal';

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

  /* ---- Sidebar state ---- */
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
  const [themeMode, setThemeMode] = useState('mono'); // 'mono', 'light', 'dark', etc.
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains('dark')
  );

  /* ---- Settings Modal ---- */
  const [settingsOpen, setSettingsOpen] = useState(false);

  /* ---- Refs ---- */
  const dirInputRef = useRef(null);
  const imageInputRef = useRef(null);

  /* ---- Theme sync ---- */
  useEffect(() => {
    // When themeMode is 'mono', it acts like a system default toggle via isDark
    // In future versions, this would handle multi-theme toggling logically
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
        isCollapsed={!sidebarOpen}
        onOpenSettings={() => setSettingsOpen(true)}
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
        activeMode={activeMode}
        onToggleSidebar={() => setSidebarOpen((s) => !s)}
      />

      {/* ---- Mode-specific input areas ---- */}
      {activeMode === 'image' && (
        <div className="flex justify-center p-4 bg-muted/30 border-b border-border">
          <div className="flex items-center gap-4 max-w-2xl w-full">
            <button
              className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 outline-none transition-colors"
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
              <div className="relative flex items-center gap-3 p-2 bg-background border border-border rounded-md shadow-sm">
                <img src={imagePreview} alt="Query preview" className="w-10 h-10 object-cover rounded shadow-sm" />
                <span className="text-sm text-foreground truncate max-w-[150px]">{imageFile?.name}</span>
                <button
                  className="p-1 text-muted-foreground hover:text-destructive transition-colors ml-2"
                  onClick={() => {
                    setImageFile(null);
                    if (imageInputRef.current) imageInputRef.current.value = '';
                  }}
                  title="Clear"
                >✕</button>
              </div>
            )}

            {imageFile && (
              <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-medium rounded-md hover:bg-primary/90 transition-colors ml-auto" onClick={handleImageSearch}>
                Search Similar
              </button>
            )}
          </div>
        </div>
      )}

      {activeMode === 'video' && (
        <div className="flex flex-col items-center justify-center p-4 bg-muted/30 border-b border-border gap-2">
          <div className="flex items-center gap-3 w-full max-w-4xl">
            <button
               className="flex items-center gap-2 px-4 py-2 shrink-0 bg-secondary text-secondary-foreground rounded-md hover:opacity-80 transition-opacity"
               onClick={() => videoInputRef.current?.click()}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}>
                 <polygon points="23 7 16 12 23 17 23 7" />
                 <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
              {videoPath ? 'Change Video' : 'Select Video'}
            </button>
            <input
              className="flex-1 h-10 px-3 rounded-md border border-input bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              type="text"
              placeholder="Paste absolute path (or click Select Video)"
              value={videoPath}
              onChange={(e) => setVideoPath(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleVideoSearch()}
            />
            <select
               value={videoFps}
               onChange={e => setVideoFps(e.target.value)}
               className="h-10 px-3 pr-8 rounded-md border border-input bg-background text-foreground"
               title="Frame Extraction Rate"
            >
               <option value="0.1">1 frame per 10s</option>
               <option value="0.2">1 frame per 5s</option>
               <option value="0.5">1 frame per 2s</option>
               <option value="1.0">1 frame per 1s</option>
               <option value="2.0">2 frames per 1s</option>
               <option value="5.0">5 frames per 1s</option>
            </select>
            <button className="h-10 px-6 font-medium font-sm rounded-md bg-primary text-primary-foreground hover:opacity-90 transition-opacity shrink-0 flex items-center justify-center" onClick={handleVideoSearch}>
              Search Frames
            </button>
          </div>
          <div className="text-sm text-muted-foreground mt-1">
            {videoPath ? `Selected: ${videoPath}` : 'Select a video and enter a text query above.'}
          </div>
        </div>
      )}

      {/* Status messages */}
      {error && (
        <div className="flex items-center justify-between mx-auto mt-4 px-4 py-3 max-w-2xl bg-destructive/15 text-destructive border border-destructive/20 rounded-md">
          <span className="font-medium text-sm">⚠ {error}</span>
          <button className="hover:opacity-70 p-1" onClick={() => setError(null)}>✕</button>
        </div>
      )}
      {successMsg && (
        <div className="flex items-center mx-auto mt-4 px-4 py-3 max-w-2xl bg-green-500/15 text-green-600 border border-green-500/20 rounded-md">
          <span className="font-medium text-sm">✓ {successMsg}</span>
        </div>
      )}
      {indexing && (
        <div className="flex items-center gap-3 mx-auto mt-4 px-4 py-3 max-w-2xl bg-blue-500/15 text-blue-600 border border-blue-500/20 rounded-md">
          <div className="w-4 h-4 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          <span className="font-medium text-sm">Indexing images… this may take a moment.</span>
        </div>
      )}

      {/* Main content area with drag-drop support */}
      <div
        className={`relative flex-1 flex flex-col min-h-0 ${isDragging ? 'ring-2 ring-primary bg-primary/5' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragging && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm border-2 border-dashed border-primary rounded-xl m-4">
            <div className="flex flex-col items-center justify-center gap-4 text-primary animate-pulse">
              <svg className="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" />
                <path d="M12 10v6" />
                <path d="m9 13 3-3 3 3" />
              </svg>
              <span className="text-2xl font-semibold">Drop folder here to index</span>
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4" onClick={() => setPlayingVideoUrl(null)}>
          <div className="relative flex flex-col items-center" onClick={e => e.stopPropagation()}>
            <video controls autoPlay src={playingVideoUrl} className="max-w-full max-h-[80vh] bg-black rounded-lg shadow-2xl" />
            <button className="absolute -top-4 -right-4 p-2 bg-black/50 hover:bg-black/80 text-white rounded-full transition-colors border border-white/20" onClick={() => setPlayingVideoUrl(null)}>
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Lightbox modal */}
      <Lightbox image={lightboxImage} onClose={handleCloseLightbox} />

      {/* Settings modal */}
      {settingsOpen && (
        <SettingsModal 
          onClose={() => setSettingsOpen(false)} 
          currentTheme={themeMode}
          onThemeChange={setThemeMode}
        />
      )}
    </Layout>
  );
}
