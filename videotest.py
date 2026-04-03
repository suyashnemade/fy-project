from core.clip_model import CLIPModel
from core.search import ImageSearcher
from PIL import Image

# 1. Load the model
print("Loading model...")
clip_model = CLIPModel()
searcher = ImageSearcher(clip_model)

# 2. Define video path and query
video_path = "E:\College\GDSC - INTRODUCTION VIDEO.mp4"  # Put your video path here
query = "beach scene"

print(f"Searching for '{query}' in {video_path}...")

# 3. Run the search (extracts 1 frame per second by default)
results = searcher.search_video(
    video_path=video_path,
    query=query,
    fps=1.0, 
    top_k=3
)

# 4. Display results
for frame_img, timestamp, score in results:
    print(f"Found match at {timestamp:.1f} seconds! (Score: {score:.4f})")
    # frame_img.show() # Uncomment this to see the actual image
