# Semantic Image Retrieval — Deep Analysis & Comparison Report

> **Date**: 17 March 2026  
> **Projects Compared**: ImageProject (Suyash Nemade) vs PerceptiText (Simran)

---

## Task 1 — System Analysis: Why Scores Are Low

### 1.1 Root Cause Analysis

After examining the codebase, evaluation scripts, and architecture, the following are the **specific causes** of the low retrieval scores (P@1 ≈ 0.27):

#### 🔴 Critical Issue: Evaluation Searches Full Flickr30k But Indexes a Subset

The evaluation script indexes images from `data/flickr30_data/flickr30k_images/` (31,783 images) but uses captions from a **subset** file. The FAISS index contains **all 31K+ images**, but only a fraction have caption-query pairs. This means:

- The search space is enormous — the correct image must be found among 31K candidates.
- CLIP ViT-B/32 zero-shot on Flickr30k typically achieves **R@1 ≈ 0.58–0.65** in published benchmarks, so P@1 ≈ 0.27 (on a subset) could be within an expected range depending on subset selection.

#### 🟡 Issue: Double Normalization

In `indexer.py` line 147, embeddings are normalized **again** after `encode_images_batch()` already normalizes them (line 104 in `clip_model.py`). While double L2-normalization of a unit vector is a no-op theoretically, it introduces floating-point drift that can subtly degrade scores.

```python
# clip_model.py line 104 — already normalizes
image_features = image_features / image_features.norm(dim=-1, keepdim=True)

# indexer.py line 147 — normalizes AGAIN
batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
```

#### 🟡 Issue: No Query Preprocessing

User text queries go directly to CLIP tokenization with no preprocessing:
- No lowercasing
- No stop-word removal  
- No prompt engineering (e.g., *"a photo of {query}"*)

CLIP was trained with specific caption styles. Adding prompt templates like `"a photo of {query}"` is documented to improve retrieval by **5–15%** in OpenAI's own findings.

#### 🟡 Issue: Model Choice

ViT-B/32 is the smallest CLIP model. Larger variants produce significantly better embeddings:

| Model | Embedding Dim | Flickr30k R@1 (zero-shot) |
|---|---|---|
| ViT-B/32 | 512 | ~58% |
| ViT-B/16 | 512 | ~65% |
| ViT-L/14 | 768 | ~74% |
| ViT-L/14@336px | 768 | ~78% |

#### 🟢 Minor: FAISS IndexFlatIP

This is actually fine for <100K images. No issue here.

### 1.2 Summary of Weaknesses

| Weakness | Impact | Fixability |
|---|---|---|
| No prompt engineering | High | Easy (1 line change) |
| Small CLIP model (ViT-B/32) | High | Easy (config change) |
| Double normalization | Low | Easy |
| No caption preprocessing | Medium | Easy |
| No reranking pipeline | High | Medium effort |
| No fine-tuning on Flickr30k | Very High | Medium effort |
| Brute-force FAISS for 30K images | None | Acceptable |

---

## Task 2 — Comparison with PerceptiText

### 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ImageProject (Your System)                        │
├─────────────────────────────────────────────────────────────────────┤
│ Model      : CLIP ViT-B/32 (zero-shot, no fine-tuning)            │
│ Text Enc   : CLIP text encoder                                     │
│ Image Enc  : CLIP image encoder                                    │
│ Index      : FAISS IndexFlatIP (cosine sim on normalized vecs)     │
│ Storage    : embeddings.npy + metadata.json + faiss.index          │
│ Search     : text→CLIP→FAISS lookup + image→CLIP→FAISS lookup     │
│ UI         : Streamlit web + CustomTkinter desktop                 │
│ Eval       : Precision@K, Recall@K, MRR, mAP (automated)          │
│ Features   : Incremental indexing, multi-dir merge, batch encoding │
│ Feedback   : ❌ None                                                │
│ Fine-tuning: ❌ None                                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       PerceptiText                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Model      : CLIP ViT-B/32 + fine-tuned on Flickr30k              │
│ Text Enc   : BERT (for caption embeddings) + CLIP (for queries)   │
│ Image Enc  : CLIP image encoder                                    │
│ Alignment  : Pre-aligned text-image embedding pairs (.npz)        │
│ Index      : sklearn cosine_similarity (brute-force numpy)         │
│ Storage    : aligned_embeddings.npz + captions_tokenized.csv       │
│ Search     : text→CLIP→cosine_similarity against image embeddings │
│ UI         : Flask web (HTML/CSS/JS)                               │
│ Eval       : ❌ No automated evaluation                            │
│ Features   : Caption suggestions, feedback buttons                 │
│ Feedback   : ✅ Yes (relevant/not_relevant logged to file)         │
│ Fine-tuning: ✅ Yes (contrastive loss, 4 epochs, AdamW 1e-5)      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Feature Comparison Table

| Feature | ImageProject (Yours) | PerceptiText |
|---|---|---|
| **CLIP Model** | ViT-B/32 (zero-shot) | ViT-B/32 (fine-tuned) |
| **Fine-tuning** | ❌ No | ✅ 4 epochs, contrastive loss |
| **Text Embeddings** | CLIP text encoder | BERT + CLIP hybrid |
| **Embedding Alignment** | Direct CLIP shared space | Pre-computed aligned .npz |
| **Vector Search** | FAISS (optimized) | sklearn cosine_similarity (slow) |
| **Incremental Indexing** | ✅ Yes | ❌ No |
| **Image-to-Image Search** | ✅ Yes | ❌ No |
| **Multi-Directory Support** | ✅ Yes | ❌ No |
| **Batch Processing** | ✅ Yes (configurable) | ❌ No |
| **User Feedback** | ❌ No | ✅ Yes (log-based) |
| **Caption Suggestions** | ❌ No | ✅ Yes (substring match) |
| **Automated Evaluation** | ✅ P@K, R@K, MRR, mAP | ❌ No |
| **Desktop App** | ✅ CustomTkinter | ❌ No |
| **Web App** | ✅ Streamlit | ✅ Flask |
| **Logging** | ✅ Rotating file logs | ❌ No |
| **Modular Architecture** | ✅ core/ package | ❌ Single file |
| **Config Management** | ✅ Centralized config.py | ❌ Hardcoded paths |
| **Unit Tests** | ✅ 39 tests (pytest) | ❌ No tests |
| **Scalability** | ✅ FAISS (millions of vectors) | ❌ numpy (max ~50K) |

### 2.3 Pros & Cons

#### Your Project — Strengths
- **Production-grade architecture**: modular `core/` package, config management, logging, error handling
- **FAISS vector search**: orders of magnitude faster than sklearn for large datasets
- **Dual UI**: both web (Streamlit) and desktop (CustomTkinter)
- **Automated evaluation pipeline**: reproducible metric computation
- **Incremental indexing**: add images without reindexing everything
- **Comprehensive testing**: 39 unit tests

#### Your Project — Weaknesses
- **No fine-tuning**: relies entirely on zero-shot CLIP
- **No user feedback mechanism**: no way to improve over time
- **No query enhancement**: raw text goes directly to CLIP
- **No reranking stage**: single-pass retrieval only

#### PerceptiText — Strengths
- **Fine-tuned CLIP**: 4-epoch contrastive training on Flickr30k improves alignment
- **User feedback UI**: relevant/not_relevant buttons with persistent logging
- **Caption autocomplete**: helps users form better queries
- **BERT text embeddings**: explored cross-encoder text representations (though not fully integrated)

#### PerceptiText — Weaknesses
- **No vector index**: uses raw numpy cosine_similarity (O(n) per query, will not scale)
- **Hardcoded absolute paths** everywhere (Windows-specific, breaks on other machines)
- **No modular architecture**: everything in one file
- **No evaluation**: no metrics computed
- **No tests, no logging, no error handling**
- **feedback_log.txt** contains concatenated HTML/CSS/JS — the file is corrupted/misused
- **Broken alignment script**: resize_embedding via truncation/padding is mathematically incorrect

### 2.4 What You Should Adopt from PerceptiText

| Idea | How to Adapt for Your Project |
|---|---|
| **Fine-tuning CLIP** | Use HuggingFace `CLIPModel` + contrastive loss on Flickr30k captions |
| **User feedback** | Add relevant/not_relevant buttons in both UIs, log to JSON |
| **Caption suggestions** | Add autocomplete from indexed captions during search |
| **Cross-encoder reranking** | Use CLIP's `logits_per_image` as a second-stage reranker |

---

## Task 3 — Improving Retrieval Accuracy

### 3.1 High-Impact Changes (Expected: +15–30% on P@1)

#### 1. Prompt Engineering (Easiest, +5–15%)

Add a prompt template before encoding text queries:

```python
# In search.py, modify the search() method:
def search(self, query: str, top_k: int = config.DEFAULT_TOP_K):
    # Add prompt template
    prompted_query = f"a photo of {query}"
    query_embedding = self.clip_model.encode_text(prompted_query)
    ...
```

CLIP was trained with caption-style text — wrapping queries improves alignment.

#### 2. Upgrade CLIP Model (Easy, +10–20%)

Change `config.py` to use a larger model:

```python
# config.py
MODEL_NAME = "ViT-L/14"  # or "ViT-L/14@336px" for best quality
EMBEDDING_DIM = 768       # update dimension
```

> **Note**: ViT-L/14 requires ~1.7GB VRAM. ViT-L/14@336px needs ~2.5GB.

#### 3. Fine-Tune CLIP on Flickr30k (+10–15%)

This is the single biggest improvement. Create a training script:

```python
# scripts/fine_tune.py (outline)
from transformers import CLIPModel, CLIPProcessor
import torch

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Use contrastive loss: for each batch, image[i] should match text[i]
# Loss = (cross_entropy(logits_per_image, labels) + 
#          cross_entropy(logits_per_text, labels)) / 2

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-6)  # Very low LR
# Train for 2-4 epochs on Flickr30k captions
```

Key parameters:
- **Learning rate**: 1e-6 (very low to avoid catastrophic forgetting)
- **Epochs**: 2–4
- **Batch size**: 16–32
- **Loss**: Symmetric contrastive loss (CLIP's native training objective)

#### 4. Remove Double Normalization (Easy Fix)

Remove the redundant normalization in `indexer.py` line 147:

```diff
-# Normalize embeddings for cosine similarity
-batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
```

The embeddings are already L2-normalized by `clip_model.py`.

### 3.2 Medium-Impact Changes

#### 5. Cross-Encoder Reranking (+5–10%)

After FAISS retrieves top-50 candidates, re-score them using CLIP's full cross-attention:

```python
# Reranking with CLIP logits
def rerank(self, query: str, candidates: List[str], top_k: int = 10):
    images = [Image.open(p) for p in candidates[:50]]
    inputs = processor(text=[query]*len(images), images=images, 
                       return_tensors="pt", padding=True)
    outputs = model(**inputs)
    scores = outputs.logits_per_text[0].softmax(dim=0)
    # Re-sort by cross-encoder scores
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
```

#### 6. Query Expansion (+3–5%)

Expand queries using synonyms or rephrasing:

```python
def expand_query(query):
    templates = [
        query,
        f"a photo of {query}",
        f"an image showing {query}",
        f"a picture depicting {query}"
    ]
    embeddings = [clip_model.encode_text(t) for t in templates]
    return np.mean(embeddings, axis=0)  # Average embedding
```

#### 7. Caption-Augmented Indexing

Store caption embeddings alongside image embeddings. When searching, also match against caption text for hybrid scoring:

```
final_score = α × image_similarity + (1-α) × caption_similarity
```

Where α = 0.7 (tunable).

---

## Task 4 — Human Feedback Learning System

### 4.1 Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
│  User Query  │───▶│  CLIP+FAISS  │───▶│  Results + UI    │
│              │    │  Retrieval   │    │  Feedback Buttons │
└─────────────┘    └──────────────┘    └────────┬─────────┘
                                                │
                                    ✅ Relevant / ❌ Not Relevant
                                                │
                                    ┌───────────▼──────────┐
                                    │  Feedback Store      │
                                    │  (feedback.json)     │
                                    └───────────┬──────────┘
                                                │
                              ┌─────────────────┼────────────────┐
                              │                 │                │
                    ┌─────────▼──────┐ ┌────────▼───────┐ ┌─────▼──────────┐
                    │ Score Boosting │ │  Learn User    │ │ Periodic       │
                    │ (immediate)   │ │  Preferences   │ │ Embedding      │
                    │               │ │  (nightly)     │ │ Re-weighting   │
                    └────────────────┘ └────────────────┘ └────────────────┘
```

### 4.2 Data Model

```python
# feedback.json structure
{
  "entries": [
    {
      "query": "sunset over mountains",
      "image_path": "data/images/12345.jpg",
      "feedback": "relevant",    # or "not_relevant"
      "timestamp": "2026-03-17T01:00:00",
      "original_rank": 3,
      "original_score": 0.254
    }
  ]
}
```

### 4.3 Three Feedback Mechanisms

#### Mechanism 1 — Immediate Score Boosting (Simple)

When a user marks an image as "relevant" for a query, boost that image's score for similar future queries:

```python
def apply_feedback_boost(results, query, feedback_store):
    boosted = []
    for path, score in results:
        boost = feedback_store.get_boost(query, path)
        # boost is +0.1 for "relevant", -0.05 for "not_relevant"
        boosted.append((path, score + boost))
    return sorted(boosted, key=lambda x: x[1], reverse=True)
```

#### Mechanism 2 — Embedding Space Adjustment (Advanced)

Use feedback to learn a **projection matrix** that warps the embedding space:

```python
# Collect positive pairs from feedback
# (query_embedding, relevant_image_embedding) → should be closer
# (query_embedding, irrelevant_image_embedding) → should be farther

# Train a small linear layer:
W = nn.Linear(512, 512)  # Learns to adjust embeddings
adjusted_query = W(query_embedding)
```

This is lightweight (512×512 = 262K parameters) and can be trained in seconds.

#### Mechanism 3 — Relevance Feedback Retrieval (Classic IR)

Implement Rocchio's feedback algorithm:

```python
def rocchio_expand(original_query_emb, relevant_embs, irrelevant_embs, 
                   alpha=1.0, beta=0.75, gamma=0.15):
    """Modify query embedding based on feedback."""
    new_query = (alpha * original_query_emb +
                 beta * np.mean(relevant_embs, axis=0) -
                 gamma * np.mean(irrelevant_embs, axis=0))
    new_query = new_query / np.linalg.norm(new_query)
    return new_query
```

### 4.4 Implementation Plan for Feedback

1. **Add UI buttons**: "👍 Relevant" and "👎 Not Relevant" on each search result
2. **Create `core/feedback.py`**: handles JSON storage, query-image scoring
3. **Modify `search.py`**: apply feedback boost after FAISS retrieval
4. **Add feedback endpoint**: `/api/feedback` for Streamlit, method for desktop

---

## Task 5 — System Architecture Improvements

### 5.1 Multi-Stage Retrieval Pipeline

```
Query ──▶ [Stage 1: FAISS Recall]     → Top 100 candidates
      ──▶ [Stage 2: Cross-Encoder]    → Top 20 reranked
      ──▶ [Stage 3: Feedback Boost]   → Top 10 final results
```

This is how production systems (Google Images, Pinterest) work. Each stage is more expensive but more precise.

### 5.2 Recommended Architecture Changes

| Component | Current | Proposed |
|---|---|---|
| **Retrieval** | Single-stage FAISS | Two-stage: FAISS recall → cross-encoder rerank |
| **Query Processing** | Raw text | Template prompting + query expansion |
| **Feedback** | None | JSON-based feedback with score boosting |
| **Caching** | None | LRU cache for query embeddings |
| **Search History** | None | Log queries + results for analytics |
| **Model Loading** | Per-request | Singleton with model warmup |

### 5.3 Caching Strategy

```python
from functools import lru_cache

class ImageSearcher:
    @lru_cache(maxsize=1000)
    def _cached_encode_text(self, query: str):
        return tuple(self.clip_model.encode_text(query).tolist())
```

### 5.4 Query Logging

```python
# core/query_logger.py
def log_query(query, results, response_time_ms):
    entry = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "num_results": len(results),
        "top_score": results[0][1] if results else 0,
        "response_time_ms": response_time_ms
    }
    # Append to search_history.json
```

This enables:
- Understanding what users search for
- Finding queries with low scores (improvement targets)
- Measuring system response time

---

## Task 6 — Future Features

### 6.1 Features That Make the Project Stand Out

| Feature | Complexity | Impact | Description |
|---|---|---|---|
| **Auto-captioning** | Medium | ✨ Very High | Use BLIP-2 to generate captions for images, enabling text+visual hybrid search |
| **Semantic Clustering** | Medium | High | Group similar images using K-means on embeddings, show "Similar Groups" in UI |
| **Query Suggestions** | Easy | High | Based on search history and existing captions |
| **Explainable Retrieval** | Medium | ✨ Very High | Show GradCAM attention maps: "why was this image retrieved?" |
| **Multi-language Search** | Easy | Medium | Use multilingual CLIP (XLM-R) for queries in Hindi, etc. |
| **Active Learning** | Hard | Very High | Use low-confidence results to request user labels |
| **Personalization** | Medium | High | User profiles that remember preferences |
| **Duplicate Detection** | Easy | Medium | Flag near-duplicate images using embedding similarity > 0.95 |

### 6.2 Explainable Retrieval (Standout Feature)

Show users **why** an image was retrieved by visualizing CLIP's attention:

```python
# Use GradCAM with CLIP's visual transformer
# Highlight the image regions that matched the query
import torch
from pytorch_grad_cam import GradCAM

# Create attention heatmap overlay on retrieved images
# Display alongside results: "These regions matched your query"
```

This is **extremely impressive** for a final year project presentation.

### 6.3 Auto-Captioning with BLIP-2

```python
from transformers import Blip2ForConditionalGeneration, Blip2Processor

# For each indexed image, generate a caption
# Store captions in metadata.json alongside paths
# Enable hybrid search: FAISS over image embeddings + text search over captions
```

---

## Task 7 — Implementation Roadmap

### 🔴 Phase 1 — High Impact (Must Implement) — 3–5 days

These changes will **immediately improve evaluation scores** by an estimated +20–30%:

| # | Task | Time | Expected Impact |
|---|---|---|---|
| 1 | Add prompt template (`"a photo of {query}"`) to `search.py` | 30 min | +5–15% P@1 |
| 2 | Remove double normalization in `indexer.py:147` | 10 min | Fixes subtle drift |
| 3 | Upgrade to ViT-L/14 model in `config.py` | 15 min | +10–20% P@1 |
| 4 | Re-run evaluation after changes 1–3 | 30 min | Measure improvement |
| 5 | Fine-tune CLIP on Flickr30k (training script) | 1–2 days | +10–15% P@1 |
| 6 | Re-run evaluation after fine-tuning | 30 min | Verify gains |

### 🟡 Phase 2 — Medium Impact — 3–5 days

| # | Task | Time | Purpose |
|---|---|---|---|
| 7 | Add user feedback system (`core/feedback.py`) | 1 day | Learn from users |
| 8 | Add feedback UI buttons to both apps | 0.5 day | UI integration |
| 9 | Implement query expansion | 0.5 day | Better retrieval |
| 10 | Add cross-encoder reranking | 1 day | Better ranking quality |
| 11 | Add query logging + search history | 0.5 day | Analytics |
| 12 | Add caption suggestions from indexed data | 0.5 day | Better UX |

### 🟢 Phase 3 — Optional Advanced Features — 5–7 days

| # | Task | Time | Purpose |
|---|---|---|---|
| 13 | Explainable retrieval (GradCAM attention) | 2 days | ✨ Presentation wow-factor |
| 14 | Auto-captioning with BLIP-2 | 1 day | Hybrid search |
| 15 | Semantic clustering visualization | 1 day | Discover image groups |
| 16 | Multi-language query support | 0.5 day | Broader accessibility |
| 17 | REST API with FastAPI | 1 day | External integration |
| 18 | Docker containerization | 0.5 day | Easy deployment |

### Priority Order

```
Week 1: Tasks 1–6 (metrics improvement)
Week 2: Tasks 7–12 (feedback + UX)
Week 3: Tasks 13–18 (advanced features, if time permits)
```

---

## Appendix: Quick Reference — Code Changes

### Change 1: Prompt Engineering (search.py)

```diff
  # In search() method, before encoding:
- query_embedding = self.clip_model.encode_text(query)
+ prompted = f"a photo of {query}"
+ query_embedding = self.clip_model.encode_text(prompted)
```

### Change 2: Remove Double Normalization (indexer.py)

```diff
  batch_embeddings = self.clip_model.encode_images_batch(batch_images)
- # Normalize embeddings for cosine similarity
- batch_embeddings = batch_embeddings / np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
```

### Change 3: Upgrade Model (config.py)

```diff
- MODEL_NAME = "ViT-B/32"
- EMBEDDING_DIM = 512
+ MODEL_NAME = "ViT-L/14"
+ EMBEDDING_DIM = 768
```

> ⚠️ **Important**: After changing the model, you must **re-index all images** because the embedding dimensions change.
