# Semantic Image Retrieval System – Evaluation Results

## Dataset Information
- **Dataset:** Flickr30k Subset  
- **Evaluation Queries:** 2000  
- **Evaluation Script Output:** query_results.csv

---

# Evaluation Metrics

## Precision@K

Precision@K measures how many of the **top K retrieved images are correct** for a given text query.

| Metric | Value | Interpretation |
|------|------|------|
| Precision@1 | 0.581 | Correct image is ranked **first in 58.1%** of queries |
| Precision@5 | 0.164 | On average **~0.82 correct images in top 5 results** |
| Precision@10 | 0.088 | On average **~0.88 correct images in top 10 results** |

### Interpretation
- The system retrieves the **correct image as the top result more than half the time**.
- This indicates good alignment between **text and image embeddings**.

---

# Recall@K

Recall@K measures whether the **correct image appears within the top K results**.

| Metric | Value | Interpretation |
|------|------|------|
| Recall@1 | 0.581 | Correct image appears at **rank 1 in 58.1%** of queries |
| Recall@5 | 0.8215 | Correct image appears in **top 5 results in 82.15%** of queries |
| Recall@10 | 0.884 | Correct image appears in **top 10 results in 88.4%** of queries |

### Interpretation
- The system successfully retrieves the correct image **within the top 5 results for most queries**.
- High recall indicates the system **rarely misses relevant images**.

---

# Mean Reciprocal Rank (MRR)

**MRR: 0.6823**

MRR evaluates **how early the correct result appears in the ranking**.

Example:

| Rank | Reciprocal Score |
|----|----|
| 1 | 1.0 |
| 2 | 0.5 |
| 3 | 0.33 |

A higher MRR means relevant results appear **closer to the top of the ranking**.

### Interpretation
- An MRR of **0.68** indicates that correct images typically appear **between rank 1 and rank 2**.

---

# Mean Average Precision (mAP)

**mAP: 0.6823**

Mean Average Precision measures **overall ranking quality across all queries**.

Typical interpretation:

| mAP | Performance |
|----|----|
| < 0.3 | Weak |
| 0.4 – 0.5 | Moderate |
| 0.6+ | Good |
| 0.7+ | Strong |

### Interpretation
- The system achieves **good ranking performance** with mAP ≈ **0.68**.
- This indicates strong semantic matching between text queries and images.

---

# Overall System Performance

The evaluation results demonstrate that the **Semantic Image Retrieval System performs effectively**.

Key observations:

- **58% Top-1 Accuracy** – The correct image is retrieved as the first result in more than half of the queries.
- **82% Recall@5** – The correct image appears within the top 5 results for most queries.
- **88% Recall@10** – The correct image is almost always retrieved within the top 10 results.
- **mAP = 0.68** – Indicates good ranking quality for retrieved results.

Overall, the system shows **strong semantic understanding between text queries and image content**, making it suitable for practical image retrieval applications.

---

# Output Files

Detailed per-query evaluation results are stored in:
