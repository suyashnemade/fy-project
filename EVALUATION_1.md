# 🎓 Project Evaluation (Revised) — Semantic Image Search

> **Project**: AI-Based Image Retrieval System Using Natural Language  
> **Team**: Atharva M. Kadu, Suyash R. Nemade, Gaurang M. Deotale, Hakimuddin I. Ali  
> **Guide**: Prof. P. G. Kale  
> **Program**: B.Tech / B.E. in AI & ML (Final Year)  
> **Evaluation Date**: 2026-03-12  

---

## What's Being Evaluated

This evaluation considers the **complete project** — not just the source code, but also the academic deliverables in the `paper/` folder:

| Deliverable | File | Status |
|-------------|------|--------|
| Literature Survey Paper | `paper/Survey_Image_Retrival_word.docx` | ✅ Complete (270-line survey, 9 sections, 26 references) |
| Project Synopsis | `paper/final Synopsis.docx` | ✅ Complete (objectives, scope, feasibility study, workflow) |
| Streamlit Web App | `app.py` | ✅ Working |
| Desktop App (CustomTkinter) | `desktop_app.py` | ✅ Working |
| Core AI Backend | `core/` modules | ✅ Working |
| Build & Packaging | `build_app.bat`, `.spec` | ✅ Present |
| Formal Evaluation Metrics | — | ❌ Missing |
| Unit Tests | — | ❌ Missing |

---

## Category-Wise Evaluation

---

### 1. Research Quality — 6.5 / 10

The previous evaluation rated this 5/10 because research documents weren't considered. The `paper/` folder **changes this significantly**.

#### What You Did Well:

- **Literature Survey** (`Survey_Image_Retrival_word.docx`) is a legitimate academic survey paper with:
  - 9 structured sections (Introduction → Traditional CBIR → Deep Learning Methods → Vision-Language Models → CLIP → Indexing/FAISS → Open Challenges → Applications → Conclusion)
  - 26 properly cited academic references spanning 2000–2024 (Smeulders 2000, He 2016, Vaswani 2017, Radford 2021, CLIPBranches 2024, etc.)
  - Covers the full evolution: handcrafted features → CNN features → Transformer-based → multimodal VLMs
  - Discusses CLIP architecture, contrastive learning, and FAISS indexing with technical depth
  - Identifies open challenges (interpretability, bias, computational cost, multilingual constraints, privacy)
  - Lists real-world applications across 6 domains (healthcare, autonomous systems, digital archives, e-commerce, education, social media)

- **Project Synopsis** (`final Synopsis.docx`) includes:
  - Feasibility study (technical, operational, economic) — well done
  - 4 clear objectives
  - Defined scope with explicit exclusions
  - Proposed system workflow for both indexing and search pipelines
  - Fundamentals section (cosine similarity, self-supervised learning, context-based embeddings)

#### What's Still Missing:

| Gap | Impact |
|-----|--------|
| **No quantitative experiments** — The survey discusses metrics conceptually but the project itself has zero evaluation results (no Precision@K, Recall@K, mAP on any benchmark) | Critical |
| **No comparison with baselines** — The survey reviews many methods but the project doesn't compare CLIP against any of them experimentally | Major |
| **Survey has some filler** — A few sections feel padded with verbose rewording of the same ideas; some references at the end (Patil 2022, Jadhav 2025) seem unrelated to image retrieval | Minor |
| **Survey is not in a proper IEEE/ACM paper format** — No abstract, no proper structure headers with standard formatting | Minor |

---

### 2. Engineering Quality — 5.5 / 10

*(Unchanged from previous evaluation — the paper folder doesn't affect code quality)*

| ✅ Good | ❌ Bad |
|---------|--------|
| Clean `core/` module separation with SRP | Zero unit tests |
| Good docstrings and type hints in core | No logging framework |
| Threading in desktop app for responsiveness | Silent exception swallowing |
| PyInstaller packaging with build scripts | Hardcoded relative paths |
| Two polished working interfaces | 1014-line monolith desktop app |
| `.gitignore` present | `storage/` binaries tracked in git |

---

### 3. Industry Relevance — 6.5 / 10

| ✅ Strengths | ⚠️ Gaps |
|-------------|---------|
| CLIP + FAISS is the actual industry stack (Pinterest, Google Photos, Shutterstock) | No REST API for integration |
| Offline / privacy-friendly = valid differentiator | No Docker / cloud deployment |
| Skills demonstrated are directly marketable | No batch processing / scalability |
| Synopsis mentions e-commerce, healthcare, digital archives use cases | These use cases aren't demonstrated |

---

## Detailed 10-Criteria Evaluation

---

### 1. Problem Statement Clarity — 7 / 10

**Improved from 6/10.** The synopsis has a clear problem statement:

> *"To create an intelligent picture retrieval system allowing users to search and retrieve pictures from large digital collections using intuitive, natural language queries rather than manual tags or set keywords."*

The synopsis also clearly defines:
- **4 Objectives** — build semantic matching pipeline, construct scalable search, evaluate accuracy, create user-friendly interface
- **Scope** — explicitly states what IS and IS NOT included
- **Exclusions** — no custom model training, no manual annotation

**Still missing:** The problem statement would be stronger with a specific motivating scenario (e.g., "A radiologist has 500K X-rays and needs to find similar cases...") and quantified pain points.

---

### 2. Novelty of the Idea — 3.5 / 10

**Slightly improved from 3/10** because the survey shows awareness of the landscape, but the implementation is still a standard CLIP+FAISS pipeline.

The synopsis honestly acknowledges this: *"existing pre-trained models are used to build fundamental functionality."*

**What would boost novelty:**
- **Fine-tuning CLIP** on a specific domain (medical, fashion, satellite)
- **Hybrid search** combining semantic search with metadata (date, geolocation, EXIF)
- **Feedback loop** where user clicks improve ranking
- **Multi-model comparison** running CLIP ViT-B/32 vs ViT-L/14 vs SigLIP vs BLIP experimentally

---

### 3. System Architecture Design — 6.5 / 10

**Good architectural decisions:**
- 3-layer architecture: Core AI → Storage → UI
- Two independent frontends share the same backend
- Synopsis describes the workflow clearly (Image Indexing → Search Pipeline → FAISS Acceleration)

**Gaps:**
- No API layer — UIs directly import core modules
- No architecture diagram in codebase or papers
- Storage is flat files (JSON + numpy) — works but not robust
- No caching (CLIP model reloaded on Streamlit reruns without session state carefully managed)

---

### 4. Choice of Models and Algorithms — 7 / 10

**Correct technology choices, well-justified in the survey:**

| Choice | Justification from Your Survey |
|--------|-------------------------------|
| CLIP ViT-B/32 | Survey discusses contrastive learning and CLIP architecture in detail (Radford 2021) |
| FAISS IndexFlatIP | Survey covers FAISS scalability (Johnson 2020), mentions billion-scale indexing |
| Cosine similarity via inner product | Synopsis has a dedicated fundamentals section explaining this |
| Offline-first design | Synopsis discusses privacy benefits for healthcare/enterprise |

**What's missing:**
- No experimental justification for choosing ViT-B/32 over ViT-L/14 or other variants
- Survey mentions FAISS IVF for scalability but implementation uses only brute-force IndexFlatIP
- No comparison with alternatives mentioned in own survey (BLIP, SigLIP, OpenCLIP)

---

### 5. Dataset Quality and Scale — 3 / 10

**This remains a critical gap:**

- No standard benchmark dataset used for evaluation
- No information about what images are in the `storage/` directory or where they came from
- Synopsis mentions *"collection and organization of an image collection"* but doesn't specify which collection
- Survey discusses datasets conceptually but no dataset is formally adopted for testing

**Minimum to fix this:** Run your system on **Flickr30K** or **MS-COCO** (both are free). Report retrieval metrics. This alone would add +1.5 points to your overall score.

---

### 6. Training Methodology — 2.5 / 10

**No training is performed.** The project uses CLIP as a black-box pretrained model.

However, the survey does demonstrate **theoretical understanding**:
- Explains contrastive learning with proper citations
- Discusses self-supervised learning paradigm
- Mentions fine-tuning as future work in the synopsis

The score is slightly improved because the survey shows you *understand* training methodology even if you don't apply it. But for an AI/ML final year project, some form of model adaptation (even lightweight fine-tuning, prompt tuning, or linear probing) would be expected.

---

### 7. Evaluation Metrics and Experiments — 2 / 10

**This is still the #1 problem with this project.**

Your own survey paper mentions retrieval evaluation metrics and discusses accuracy — but your actual project has **zero quantitative results**. This creates a disconnect between what you write about and what you actually measure.

No Precision@K, Recall@K, mAP, NDCG, MRR — nothing. No benchmark. No baseline. No comparison table. No confusion matrix. No qualitative failure analysis.

**For an AI/ML project, this is the equivalent of submitting a science experiment without recording any results.**

---

### 8. Real-World Usability — 7 / 10

**Strongest area.** Two working interfaces, good UX, offline capability, packaged as `.exe`.

The desktop app is genuinely impressive for a college project:
- Dark theme with custom colors
- Image lightbox with metadata
- Context menus (right-click → Open in Explorer, Copy Path)
- Search history
- Progress bars with threaded operations
- Tooltips throughout

---

### 9. Scalability and Deployment Feasibility — 4.5 / 10

Synopsis discusses scalability:
- Mentions FAISS for billion-scale indexing
- Mentions GPU acceleration as optional
- Discusses economic feasibility of open-source stack

But implementation doesn't deliver on these claims:
- Brute-force FAISS index (no IVF, no HNSW)
- No batch processing (images encoded one-at-a-time)
- No Docker deployment
- No API endpoints
- Single-user only

**The gap between what the synopsis promises and what the code delivers hurts this score.**

---

### 10. Code Structure and Engineering Practices — 5.5 / 10

| Practice | Status |
|----------|--------|
| Modular package structure | ✅ |
| Type hints | ✅ (core only) |
| Docstrings | ✅ (core only) |
| `.gitignore` | ✅ (incomplete) |
| Build scripts | ✅ |
| Unit tests | ❌ None |
| Logging | ❌ None |
| CI/CD | ❌ None |
| Linting | ❌ None |
| Configuration management | ❌ Hardcoded |

---

## Conceptual & Technical Flaws

### 🔴 Conceptual Flaws

| # | Flaw | Explanation |
|---|------|-------------|
| 1 | **Claims without evidence** | Synopsis says the system provides "strong retrieval" and "high accuracy" but no metrics are presented to support this. In academia, this is a red flag. |
| 2 | **Survey-implementation disconnect** | The survey extensively discusses evaluation metrics, baselines, and benchmark datasets, but the actual project implements none of them. An evaluator will notice this contradiction. |
| 3 | **Zero-shot used incorrectly** | The synopsis mentions "zero-shot" capability as if it's a feature you built, but it's an inherent property of CLIP's pretraining. You didn't build zero-shot capability — you just used a model that has it by default. |
| 4 | **Scope mismatch in requirements** | Synopsis mentions TensorFlow, Scikit-Learn, Flask, FastAPI, Pandas, Jupyter — none of these are actually used in the project. The requirements list technologies you planned to use but didn't. |
| 5 | **Feasibility study is theoretical** | Economic and operational feasibility sections read well but aren't backed by actual deployment data (no load testing, no cost analysis, no user testing). |

### 🟡 Technical Flaws

| # | Flaw | Impact |
|---|------|--------|
| 1 | **Hardcoded relative paths** | `Path('storage/...')` breaks if run from a different working directory |
| 2 | **No incremental indexing** | Re-indexing destroys the old index; can't add images to existing collection |
| 3 | **Silent error swallowing** | `except Exception: continue` hides real bugs during indexing |
| 4 | **CLIP token limit not enforced** | Queries longer than 77 tokens are silently truncated without warning the user |
| 5 | **No input validation** | Empty queries, special characters, extremely long queries are not handled |
| 6 | **Single-threaded encoding** | Images encoded one-at-a-time; CLIP supports batch encoding (5-10× faster on GPU) |
| 7 | **No deduplication** | Same image indexed multiple times if directory is re-scanned |
| 8 | **`storage/` binaries in git** | 2MB+ of `.npy` and `.index` files are tracked in version control |
| 9 | **`fix_quotes.py`  in repository** | Debug script doesn't belong in production codebase |
| 10 | **Desktop app monolith** | 1014 lines in one file — should be split into UI components, business logic, and event handlers |

---

## Final Rating

| Category | Weight | Score | Weighted |
|----------|--------|-------|----------|
| Research Quality | 15% | 6.5 | 0.975 |
| Engineering Quality | 15% | 5.5 | 0.825 |
| Industry Relevance | 10% | 6.5 | 0.650 |
| Problem Statement Clarity | 5% | 7.0 | 0.350 |
| Novelty | 10% | 3.5 | 0.350 |
| System Architecture | 10% | 6.5 | 0.650 |
| Model & Algorithm Choice | 5% | 7.0 | 0.350 |
| Dataset & Evaluation | 15% | 2.5 | 0.375 |
| Real-World Usability | 5% | 7.0 | 0.350 |
| Scalability & Deployment | 5% | 4.5 | 0.225 |
| Code & Engineering | 5% | 5.5 | 0.275 |
| | | **Total** | **5.375** |

### **Final Score: 5.5 / 10**

> *Adjusted up from 5.0 due to the literature survey and synopsis — the research groundwork EXISTS, it just needs to be connected to actual experimental results.*

---

### Where You Stand

| Tier | Range | Description | You? |
|------|-------|-------------|------|
| **S-Tier** | 9-10 | Novel contribution, published/publishable, exceptional engineering | ❌ |
| **A-Tier** | 7-8 | Rigorous evaluation, clean engineering, some novelty or depth | ❌ |
| **B-Tier** | 5-6 | Working app with standard techniques, decent code, some research docs | ✅ **You are here (upper B)** |
| **C-Tier** | 3-4 | Basic/broken implementation, poor code quality | ❌ |

**For college:** This gets you a solid **B+ grade**. Working application + survey paper + synopsis = you clearly did work. But the missing evaluation metrics stop it from being an A.

---

## 🛠️ How to Improve — Prioritized Action Plan

### 🔴 Priority 1: Add Evaluation (Most Impact — could add +1.5 to score)

This is the single most impactful thing you can do. Your survey discusses metrics, your synopsis promises evaluation — now DELIVER on it.

**Step 1: Download Flickr30K or MS-COCO test set**
```bash
# Flickr30K (smaller, easier to start with)
# Download from: https://www.kaggle.com/datasets/hsankesara/flickr-image-dataset
```

**Step 2: Create an evaluation script**
```python
# evaluation/evaluate.py
import time
from core.clip_model import CLIPModel
from core.indexer import ImageIndexer
from core.search import ImageSearcher

def precision_at_k(ground_truth_path, retrieved_paths, k):
    """What fraction of top-K results are correct?"""
    top_k = retrieved_paths[:k]
    hits = sum(1 for p in top_k if p == ground_truth_path)
    return hits / k

def recall_at_k(ground_truth_path, retrieved_paths, k):
    """Is the correct image found in top-K?"""
    top_k = retrieved_paths[:k]
    return 1.0 if ground_truth_path in top_k else 0.0

def reciprocal_rank(ground_truth_path, retrieved_paths):
    """At what rank is the correct image found?"""
    for i, p in enumerate(retrieved_paths):
        if p == ground_truth_path:
            return 1.0 / (i + 1)
    return 0.0

def evaluate(image_dir, captions_file, k_values=[1, 5, 10]):
    """
    Full evaluation on a captioned dataset.
    Report: Precision@K, Recall@K, MRR for each K value.
    """
    # 1. Index all images
    # 2. For each (image, caption) pair:
    #    - Search using the caption
    #    - Check if the correct image appears in results
    # 3. Average metrics across all queries
    # 4. Print results table
    pass
```

**Step 3: Present results in a table**
```
| Metric          | K=1   | K=5   | K=10  |
|-----------------|-------|-------|-------|
| Precision@K     | 0.XX  | 0.XX  | 0.XX  |
| Recall@K        | 0.XX  | 0.XX  | 0.XX  |
| MRR             | 0.XX  | —     | —     |
```

**Step 4: Compare at least 2 configurations**
```
| Model         | P@1  | P@5  | P@10 | Search Time (ms) |
|---------------|------|------|------|-------------------|
| CLIP ViT-B/32 | 0.XX | 0.XX | 0.XX | XX                |
| CLIP ViT-L/14 | 0.XX | 0.XX | 0.XX | XX                |
```

---

### 🟡 Priority 2: Fix the Survey-Implementation Gaps (Credibility — +0.5)

Your survey and synopsis mention tools/features that aren't in your code. Fix this:

| Claimed in Synopsis | Actually Used | Fix |
|---------------------|---------------|-----|
| TensorFlow | ❌ Not used | Remove from requirements section |
| Scikit-Learn | ❌ Not used | Remove from requirements section |
| Flask / FastAPI | ❌ Used Streamlit instead | Update synopsis or add a FastAPI endpoint |
| Pandas | ❌ Not used | Remove or use for evaluation data handling |
| Jupyter Notebook | ❌ Not present | Add a demo notebook or remove claim |

Either update the synopsis to match reality, or add these features to make the synopsis truthful.

---

### 🟡 Priority 3: Add Unit Tests (Engineering — +0.5)

```
tests/
├── __init__.py
├── test_clip_model.py    # Test encode_image returns 512-d vector, etc.
├── test_indexer.py        # Test indexing a small directory
├── test_search.py         # Test search returns sorted results
├── test_utils.py          # Test file discovery, metadata I/O
└── fixtures/
    └── sample_images/     # 5 small test images
```

Add `pytest` to `requirements.txt` and include a `Makefile` or script to run tests:
```bash
pytest tests/ -v --tb=short
```

---

### 🟢 Priority 4: Add One Novel Feature (+0.5)

**Recommended: Image-to-Image Search** — easiest to implement since you already have `encode_image()`:

```python
# In search.py, add:
def search_by_image(self, query_image: Image.Image, top_k: int = 10):
    """Reverse image search — find similar images."""
    query_embedding = self.clip_model.encode_image(query_image)
    query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
    scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        image_id = str(idx)
        if image_id in self.metadata:
            results.append((self.metadata[image_id], float(score)))
    return results
```

Then add an "Upload Image" button in both UIs. This feature would genuinely differentiate your project.

---

### 🟢 Priority 5: Embedding Visualization (Presentation Polish — +0.25)

Create a t-SNE or UMAP visualization of your image embeddings. This looks incredible on slides:

```python
# visualization/visualize_embeddings.py
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

embeddings = np.load('storage/embeddings.npy')
tsne = TSNE(n_components=2, perplexity=30, random_state=42)
reduced = tsne.fit_transform(embeddings)

plt.figure(figsize=(12, 8))
plt.scatter(reduced[:, 0], reduced[:, 1], alpha=0.5, s=10)
plt.title('Image Embedding Space (t-SNE)')
plt.savefig('embedding_visualization.png', dpi=150)
plt.show()
```

Color-code by image category if you have labeled data — this creates a visually stunning plot that shows semantic clustering.

---

## Summary Table: Current vs Improved

| Area | Current Score | After Fixes | What to Do |
|------|---------------|-------------|------------|
| Evaluation Metrics | 2.0 | 6.0 | Run evaluation on Flickr30K with P@K, R@K, MRR |
| Novelty | 3.5 | 5.0 | Add image-to-image search |
| Engineering | 5.5 | 7.0 | Add tests, logging, fix paths |
| Research | 6.5 | 7.5 | Add experiment results to supplement survey |
| **Overall** | **5.5** | **~7.0** | — |

**Doing just Priority 1 (evaluation) and Priority 4 (image-to-image search) over 1-2 weeks would push this project into A-tier territory (7+).**

---

## 💡 Viva / Presentation Tips

1. **Lead with the demo** — Show the desktop app searching real images live. First impressions matter.
2. **Show your survey knowledge** — When asked about CLIP, explain contrastive learning (image-text pairs, InfoNCE loss, shared embedding space). This shows depth beyond just using the API.
3. **Be honest about limitations** — Proactively mention: "We used pretrained CLIP without fine-tuning. For domain-specific accuracy, fine-tuning would help." Evaluators respect this.
4. **Have failure cases ready** — Show examples where the search fails (e.g., CLIP struggles with counting, spatial relationships, fine-grained distinctions). Explain WHY.
5. **Know your numbers** — "We indexed X images in Y seconds. Search takes Z milliseconds. Our embedding dimension is 512." Concrete numbers sound professional.
6. **Relate survey to implementation** — "As discussed in our survey, Radford et al. 2021 demonstrated CLIP's zero-shot transfer capabilities. We leverage this by using the pretrained ViT-B/32 variant which maps both images and text to a 512-dimensional shared space."

---

> **Bottom Line**: You've built a working system with a solid literature foundation. The survey paper and synopsis show real academic effort. The main gap is the **bridge between your research and your implementation** — your survey discusses evaluation methods that your project doesn't implement. Close that gap with actual metrics on a real benchmark, and this becomes a genuinely strong final year project.
