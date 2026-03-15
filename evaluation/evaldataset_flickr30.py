import shutil
import os
import random
import csv
from pathlib import Path

# Config
NUM_IMAGES_TO_SAMPLE = 2000  # Change this to sample more/less

# Source paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_IMG_DIR = PROJECT_ROOT / "data" / "flickr30_data" / "flickr30k_images"
SRC_CAPTION_FILE = PROJECT_ROOT / "data" / "flickr30_data" / "captions.txt"

# Destination paths
DST_DIR = PROJECT_ROOT / "evaluation" / "data" / "flickr_subset"
DST_IMG_DIR = DST_DIR / "images"
DST_CAPTION_FILE = DST_DIR / "captions.txt"

def create_subset():
    print(f"Creating evaluation subset of {NUM_IMAGES_TO_SAMPLE} images...")
    
    if not SRC_IMG_DIR.exists() or not SRC_CAPTION_FILE.exists():
        print("Error: Source data not found. Make sure 'data/flick30 data' exists.")
        return

    # 1. Clean and recreate destination directories
    if DST_DIR.exists():
        shutil.rmtree(DST_DIR)
    DST_IMG_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Sample images
    all_images = [f for f in os.listdir(SRC_IMG_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    sample_size = min(NUM_IMAGES_TO_SAMPLE, len(all_images))
    
    if sample_size == 0:
        print("No images found in the source directory.")
        return
        
    sampled_images = random.sample(all_images, sample_size)
    print(f"Sampled {len(sampled_images)} images out of {len(all_images)} available.")

    # 3. Copy images
    for img in sampled_images:
        shutil.copy2(SRC_IMG_DIR / img, DST_IMG_DIR / img)
    print(f"Copied {len(sampled_images)} images to {DST_IMG_DIR}")

    # 4. Copy matching captions
    selected_set = set(sampled_images)
    written_count = 0

    with open(SRC_CAPTION_FILE, "r", encoding="utf-8") as f_in, \
         open(DST_CAPTION_FILE, "w", encoding="utf-8", newline="") as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        # Keep header if present
        header = next(reader, None)
        if header:
            writer.writerow(header)
            
        for row in reader:
            if len(row) >= 2:
                img_name = row[0].strip()
                if img_name in selected_set:
                    writer.writerow(row)
                    written_count += 1

    print(f"Extracted {written_count} captions to {DST_CAPTION_FILE}")
    print("\nSubset creation complete!")
    print(f"Run evaluation using: python -m evaluation.evaluate --dataset evaluation/data/flickr_subset")

if __name__ == "__main__":
    create_subset()