"""
Evaluation script for the Semantic Image Retrieval system.
Computes Precision@K, Recall@K, MRR, and mAP on the Flickr30k dataset subset.
"""

import os
import csv
import sys
from pathlib import Path
from datetime import datetime
# Add project root to path so we can import 'core'
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from core import config

# -------------------------------------------------------------------------
# Override configurations specifically for evaluation
# This ensures we don't overwrite the user's primary application index
# -------------------------------------------------------------------------
eval_storage = project_root / "evaluation" / "storage"
eval_storage.mkdir(parents=True, exist_ok=True)

config.STORAGE_DIR = eval_storage
config.EMBEDDINGS_PATH = config.STORAGE_DIR / "embeddings.npy"
config.METADATA_PATH = config.STORAGE_DIR / "metadata.json"
config.FAISS_INDEX_PATH = config.STORAGE_DIR / "faiss.index"
config.FEEDBACK_PATH = config.STORAGE_DIR / "feedback.json"
config.MODEL_FINGERPRINT_PATH = config.STORAGE_DIR / "model_fingerprint.json"

eval_logs = project_root / "evaluation" / "logs"
eval_logs.mkdir(parents=True, exist_ok=True)
config.LOGS_DIR = eval_logs
timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
config.LOG_FILE = config.LOGS_DIR / f"evaluation_{timestamp}.log"

# Now we can safely import core components that use config
from core.logger import get_logger
from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher

logger = get_logger(__name__)

def clean_eval_storage():
    """Removes old evaluation indices to ensure a fresh evaluation."""
    paths = [config.EMBEDDINGS_PATH, config.METADATA_PATH, config.FAISS_INDEX_PATH]
    for p in paths:
        if p.exists():
            p.unlink()

def evaluate(dataset_dir: str):
    """
    Evaluates the system using images and captions from the given directory.
    Uses Precision@K, Recall@K, MRR, and mAP.
    """
    base_dir = Path(dataset_dir)
    images_dir = base_dir / "flickr30k_images"
    if not images_dir.exists():
        # Fallback for subset directories
        images_dir = project_root / "data" / "flickr30_data" / "flickr30k_images"
        
    captions_file = project_root / "data" / "flickr30_data" / "captions.txt"

    if not images_dir.exists() or not captions_file.exists():
        logger.error(f"Dataset not found. Expected '{images_dir.name}' and 'captions.txt' in {base_dir}")
        return

    #logger.info("Cleaning old evaluation index...")
    #clean_eval_storage()

    logger.info("Loading CLIP model...")
    clip_model = CLIPModel(device=None)

    if not config.FAISS_INDEX_PATH.exists():
        logger.info("FAISS index not found. Building index...")

        indexer = ImageIndexer(clip_model)

        def index_progress(cur, tot):
            if cur % 50 == 0 or cur == tot:
                logger.info(f"Indexed {cur}/{tot} images...")

        successful, failed = indexer.index_directory(
            str(images_dir),
            progress_callback=index_progress
        )

        logger.info(f"Indexing complete: {successful} indexed, {failed} failed.")

    else:
        logger.info("Existing FAISS index found. Skipping indexing.")

    logger.info("Loading FAISS index for search...")
    searcher = ImageSearcher(clip_model)

    # Parse captions. We use 1 caption per image to create query-ground-truth pairs.
    query_image_map = []
    seen_images = set()

    with open(captions_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            next(reader) # skip header if present
        except StopIteration:
            pass
            
        for row in reader:
            if len(row) >= 2:
                img_name = row[0].strip()
                caption = row[1].strip()
                img_path = images_dir / img_name
                
                # We only take the first caption for each image to keep it 1:1 for this evaluation.
                if img_path.exists() and img_name not in seen_images:
                    query_image_map.append((caption, str(img_path)))
                    seen_images.add(img_name)

    total_queries = len(query_image_map)
    logger.info(f"Loaded {total_queries} queries (1 caption per image).")

    if total_queries == 0:
        logger.error("No valid queries found to evaluate.")
        return

    # Initialize metrics
    K_VALUES = [1, 5, 10]
    results = {
        "P@1": 0.0, "P@5": 0.0, "P@10": 0.0,
        "R@1": 0.0, "R@5": 0.0, "R@10": 0.0,
        "MRR": 0.0, "mAP": 0.0
    }

    logger.info("Starting evaluation queries...")
    max_k = max(K_VALUES)
    
    # Optional: write results to a CSV
    results_csv_path = project_root / "evaluation" / "query_results.csv"
    
    with open(results_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["query", "ground_truth", "found_at_rank", "P@1", "P@5", "P@10", "RR"])
        
        for i, (query, ground_truth_path) in enumerate(query_image_map):
            search_results = searcher.search(query, top_k=max_k)
            retrieved_names = [Path(res[0]).name for res in search_results]
            gt_name = Path(ground_truth_path).name

            found_at_rank = -1
            for rank, name in enumerate(retrieved_names, 1):
                if name == gt_name:
                    found_at_rank = rank
                    break

            # Metrics for this query
            reciprocal_rank = (1.0 / found_at_rank) if found_at_rank != -1 else 0.0
            results["MRR"] += reciprocal_rank
            results["mAP"] += reciprocal_rank # For exactly 1 relevant item, AP = RR
            
            row_data = [query, gt_name, found_at_rank]
            
            for k in K_VALUES:
                if found_at_rank != -1 and found_at_rank <= k:
                    results[f"R@{k}"] += 1.0
                    results[f"P@{k}"] += 1.0 / k  # 1 relevant item in top K means precision is 1/K
                    row_data.append(1.0/k)
                else:
                    row_data.append(0.0)
            
            row_data.append(reciprocal_rank)
            writer.writerow(row_data)

            if (i + 1) % 50 == 0 or (i + 1) == total_queries:
                logger.info(f"Processed {i + 1}/{total_queries} queries...")

    # Average the metrics
    for k in results.keys():
        results[k] /= total_queries


    # ------------------------------------------------------------------
    # Save experiment summary
    # ------------------------------------------------------------------

    results_dir = project_root / "evaluation" / "results"
    results_dir.mkdir(exist_ok=True)

    existing = list(results_dir.glob("experiment_*_results.csv"))
    experiment_num = len(existing) + 1

    experiment_file = results_dir / f"experiment_{experiment_num}_results.csv"

    timestamp = datetime.now()
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M:%S")

    num_images = len(os.listdir(images_dir))

    row = [
        date_str,
        time_str,
        str(dataset_dir),
        num_images,
        total_queries,
        results["P@1"],
        results["P@5"],
        results["P@10"],
        results["R@1"],
        results["R@5"],
        results["R@10"],
        results["MRR"],
        results["mAP"]
    ]

    file_exists = experiment_file.exists()

    with open(experiment_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "date",
                "time",
                "dataset",
                "num_images",
                "num_queries",
                "P@1",
                "P@5",
                "P@10",
                "R@1",
                "R@5",
                "R@10",
                "MRR",
                "mAP"
            ])

        writer.writerow(row)

    print(f"Experiment results saved to: {experiment_file}")
    # Print final summary
    print("\n" + "="*50)
    print(" " * 15 + "EVALUATION RESULTS")
    print("="*50)
    print(f"Dataset      : {dataset_dir}")
    print(f"Total Queries: {total_queries}")
    print("-" * 50)
    for k in K_VALUES:
        print(f"Precision@{k:2d}: {results[f'P@{k}']:.4f}")
    print("-" * 50)
    for k in K_VALUES:
        print(f"Recall@{k:2d}   : {results[f'R@{k}']:.4f}")
    print("-" * 50)
    print(f"MRR          : {results['MRR']:.4f}")
    print(f"mAP          : {results['mAP']:.4f}")
    print("="*50)
    print(f"Detailed query results saved to: {results_csv_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate semantic image retrieval")
    parser.add_argument(
        "--dataset", 
        type=str, 
        default="data/flickr30_data",
        help="Path to the dataset directory (relative to project root)"
    )
    args = parser.parse_args()
    
    dataset_path = project_root / args.dataset
    evaluate(str(dataset_path))
