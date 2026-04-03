"""
Video Scene Search feature module.

Extracts frames from a video at a configurable FPS, encodes them using CLIP,
and finds frames most relevant to a text query. Lightweight and modular —
reuses the existing CLIP embedding pipeline.

Requires: opencv-python (cv2). Gracefully handles missing dependency.
"""

import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

from ..logger import get_logger
from .. import config

logger = get_logger(__name__)


def _check_cv2():
    """Check if OpenCV is available, raise helpful error if not."""
    try:
        import cv2
        return cv2
    except ImportError:
        raise ImportError(
            "Video search requires opencv-python. "
            "Install it with: pip install opencv-python"
        )


def extract_frames(
    video_path: str,
    fps: float = 1.0,
    max_frames: int = 300,
) -> List[Tuple[Image.Image, float]]:
    """
    Extract frames from a video file at a specified frame rate.

    Args:
        video_path: Path to the video file
        fps: Frames per second to extract (default: 1 frame/second)
        max_frames: Maximum number of frames to extract (safety limit)

    Returns:
        List of (PIL Image, timestamp_seconds) tuples

    Raises:
        ImportError: If opencv-python is not installed
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened
    """
    cv2 = _check_cv2()

    video_path = str(video_path)
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    try:
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if video_fps <= 0:
            logger.warning(f"Could not determine video FPS, assuming 30.")
            video_fps = 30.0

        # Calculate frame interval: how many video frames to skip between extractions
        frame_interval = max(1, int(video_fps / fps))
        duration = total_frames / video_fps

        logger.info(
            f"Video: {Path(video_path).name}, "
            f"{video_fps:.1f} fps, {total_frames} frames, "
            f"{duration:.1f}s duration, extracting every {frame_interval} frames"
        )

        frames: List[Tuple[Image.Image, float]] = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                # Convert BGR (OpenCV) → RGB (PIL)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                timestamp = frame_idx / video_fps

                frames.append((pil_image, timestamp))

                if len(frames) >= max_frames:
                    logger.warning(
                        f"Reached max_frames limit ({max_frames}). "
                        f"Stopping extraction at {timestamp:.1f}s."
                    )
                    break

            frame_idx += 1

        logger.info(f"Extracted {len(frames)} frames from {Path(video_path).name}")
        return frames

    finally:
        cap.release()


def search_video(
    clip_model,
    video_path: str,
    query: str,
    fps: float = 1.0,
    top_k: int = 5,
    max_frames: int = 300,
    batch_size: int = 32,
) -> List[Tuple[Image.Image, float, float]]:
    """
    Search a video for frames matching a text query.

    Pipeline:
        1. Extract frames at specified FPS
        2. Batch-encode frames using CLIP image encoder
        3. Encode query text using CLIP text encoder
        4. Compute cosine similarity between query and all frames
        5. Return top-k matching frames with timestamps

    Args:
        clip_model: CLIPModel instance
        video_path: Path to the video file
        query: Text query describing what to find
        fps: Frame extraction rate (frames per second, default: 1)
        top_k: Number of top matching frames to return
        max_frames: Maximum frames to extract (safety limit)
        batch_size: Batch size for encoding frames

    Returns:
        List of (frame_image, timestamp_seconds, similarity_score) tuples,
        sorted by descending similarity score

    Raises:
        ImportError: If opencv-python is not installed
        FileNotFoundError: If video file doesn't exist
    """
    # Extract frames
    frames = extract_frames(video_path, fps=fps, max_frames=max_frames)

    if not frames:
        logger.warning(f"No frames extracted from {video_path}")
        return []

    logger.info(f"Encoding {len(frames)} frames for query: '{query}'")

    # Encode query text
    query_embedding = clip_model.encode_text(f"a photo of {query}")
    query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

    # Batch-encode all frames
    all_frame_embeddings = []
    frame_images = [frame for frame, _ in frames]

    for i in range(0, len(frame_images), batch_size):
        batch = frame_images[i:i + batch_size]
        try:
            batch_embeddings = clip_model.encode_images_batch(batch)
            all_frame_embeddings.append(batch_embeddings)
        except Exception as e:
            logger.error(f"Failed to encode frame batch {i}: {e}")
            continue

    if not all_frame_embeddings:
        logger.error("No frames were successfully encoded.")
        return []

    frame_embeddings = np.vstack(all_frame_embeddings).astype(np.float32)

    # Compute cosine similarities (embeddings are already normalized)
    similarities = (frame_embeddings @ query_embedding.T).flatten()

    # Get top-k indices
    actual_k = min(top_k, len(similarities))
    top_indices = np.argsort(similarities)[::-1][:actual_k]

    # Build results
    results = []
    for idx in top_indices:
        frame_img, timestamp = frames[idx]
        score = float(similarities[idx])
        results.append((frame_img, timestamp, score))

    logger.info(
        f"Video search complete: top score={results[0][2]:.4f} "
        f"at t={results[0][1]:.1f}s" if results else "No results"
    )

    return results


def format_timestamp(seconds: float) -> str:
    """
    Format seconds into a human-readable timestamp string (HH:MM:SS).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"
