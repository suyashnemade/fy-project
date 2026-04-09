/**
 * api.js — All backend API calls in one place.
 *
 * Every function returns { data, error } so the caller can handle both cases.
 * Uses fetch() with async/await. No external libraries.
 */

const API_BASE = 'http://localhost:8000';

// ── Helpers ────────────────────────────────────────────────────────────────

async function request(url, options = {}) {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message = body.detail || `Server error (${response.status})`;
      return { data: null, error: message };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (err) {
    // Network error (backend not running, CORS, etc.)
    return { data: null, error: `Cannot reach server: ${err.message}` };
  }
}

// ── Health / Status ────────────────────────────────────────────────────────

/**
 * Check if the backend is alive and models are loaded.
 * GET /
 */
export async function healthCheck() {
  return request(`${API_BASE}/`);
}

/**
 * Get current FAISS index info (count, size, ready).
 * GET /index/status
 */
export async function getIndexStatus() {
  return request(`${API_BASE}/index/status`);
}

// ── Search ─────────────────────────────────────────────────────────────────

/**
 * Text-to-image search.
 * GET /search/text?query=...&top_k=...
 */
export async function searchByText(query, topK = 10) {
  const params = new URLSearchParams({ query, top_k: topK });
  return request(`${API_BASE}/search/text?${params}`);
}

/**
 * Image-to-image search (file upload).
 * POST /search/image
 */
export async function searchByImage(file, topK = 10) {
  const formData = new FormData();
  formData.append('file', file);

  const params = new URLSearchParams({ top_k: topK });
  return request(`${API_BASE}/search/image?${params}`, {
    method: 'POST',
    body: formData,
  });
}

/**
 * Video frame search.
 * POST /search/video  { video_path, query, top_k, fps }
 */
export async function searchVideo({ videoPath, query, topK = 5, fps = 1.0 }) {
  return request(`${API_BASE}/search/video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      video_path: videoPath,
      query,
      top_k: topK,
      fps,
    }),
  });
}

// ── Indexing ───────────────────────────────────────────────────────────────

/**
 * Index all images in a directory.
 * POST /index/directory  { directory: "..." }
 */
export async function indexDirectory(directory) {
  return request(`${API_BASE}/index/directory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ directory }),
  });
}

/**
 * Extract and encode frames from a video.
 * POST /index/video  { video_path: "...", fps: 1.0 }
 */
export async function indexVideo({ videoPath, fps = 1.0 }) {
  return request(`${API_BASE}/index/video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_path: videoPath, fps }),
  });
}

/**
 * Clear the entire FAISS index and SQLite DB physically from disk.
 * DELETE /index/clear
 */
export async function clearIndex() {
  return request(`${API_BASE}/index/clear`, {
    method: 'DELETE',
  });
}

// ── Image serving ──────────────────────────────────────────────────────────

/**
 * Build a URL to load an image from the backend.
 * GET /files/image?path=...
 *
 * This returns a URL string, NOT a fetch call,
 * because <img src="..."> handles the loading.
 */
export function getImageUrl(absolutePath) {
  const params = new URLSearchParams({ path: absolutePath });
  return `${API_BASE}/files/image?${params}`;
}

/**
 * Build a URL to load and play a video from a specific timestamp.
 */
export function getVideoUrl(absolutePath, timestamp) {
  const params = new URLSearchParams({ path: absolutePath });
  const base = `${API_BASE}/files/video?${params}`;
  return timestamp ? `${base}#t=${timestamp}` : base;
}

// ── Feedback ───────────────────────────────────────────────────────────────

/**
 * Submit relevance feedback for a search result.
 * POST /feedback/add
 */
export async function addFeedback({ query, imagePath, feedback, rank, score }) {
  return request(`${API_BASE}/feedback/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      image_path: imagePath,
      feedback,
      rank: rank ?? -1,
      score: score ?? 0,
    }),
  });
}

/**
 * Get feedback statistics.
 * GET /feedback/stats
 */
export async function getFeedbackStats() {
  return request(`${API_BASE}/feedback/stats`);
}

// ── Explainability ─────────────────────────────────────────────────────────

/**
 * Generate visual explanation for a search result.
 * POST /explain/result
 */
export async function explainResult(imagePath, query) {
  return request(`${API_BASE}/explain/result`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_path: imagePath, query }),
  });
}

// ── System Dialogs ────────────────────────────────────────────────────────

/**
 * Open a native file dialog on the backend host to select a file.
 * GET /system/select-file
 */
export async function selectSystemFile(filetypes = ".mp4,.avi,.mkv,.webm") {
  const params = new URLSearchParams({ filetypes });
  return request(`${API_BASE}/system/select-file?${params}`);
}

/**
 * Open a native directory dialog on the backend host.
 * GET /system/select-directory
 */
export async function selectSystemDirectory() {
  return request(`${API_BASE}/system/select-directory`);
}

/**
 * Send a stop signal to cancel any ongoing indexing or video processing operations.
 * POST /system/stop
 */
export async function stopProcessing() {
  return request(`${API_BASE}/system/stop`, {
    method: 'POST',
  });
}

