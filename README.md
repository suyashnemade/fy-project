# Semantic Image Search Application

An offline semantic image search application built with CLIP (ViT-B/32) and FAISS. Search through your local image collection using natural language queries.

## Features

- **Offline Operation**: Works completely offline after installation
- **Semantic Search**: Uses CLIP to understand both images and text queries
- **Fast Retrieval**: FAISS index for efficient similarity search
- **Simple Interface**: Clean Streamlit UI for indexing and searching

## Requirements

- Python 3.8 or higher
- ~1GB disk space for CLIP model download (first run)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

The application will open in your default web browser.

## Usage

### Indexing Images

1. In the sidebar, enter the path to a directory containing images
2. Click "Index Images" button
3. Wait for indexing to complete (progress bar will show status)

**Supported formats**: JPG, JPEG, PNG (case-insensitive)

### Searching Images

1. Ensure images have been indexed (check sidebar status)
2. Enter a natural language query in the search box
   - Examples:
     - "a cat sitting on a couch"
     - "sunset over mountains"
     - "red sports car"
     - "people playing basketball"
3. Adjust the number of results using the slider (1-50)
4. Click "Search" button
5. Results are displayed in a grid with similarity scores

## Project Structure

```
image_search_app/
├── app.py                 # Streamlit entry point
├── core/
│   ├── __init__.py
│   ├── clip_model.py      # CLIP model loading and encoding
│   ├── indexer.py         # Image indexing and FAISS index creation
│   ├── search.py          # FAISS similarity search
│   └── utils.py           # Utility functions
├── storage/               # Generated files (embeddings, index, metadata)
├── data/
│   └── sample_images/     # Optional test images
├── requirements.txt
└── README.md
```

## Technical Details

- **Model**: CLIP ViT-B/32 (pretrained, no fine-tuning)
- **Embeddings**: 512-dimensional normalized vectors
- **Index**: FAISS IndexFlatIP (inner product on normalized vectors = cosine similarity)
- **Storage**: 
  - `embeddings.npy`: NumPy array of image embeddings
  - `faiss.index`: FAISS index file
  - `metadata.json`: Mapping from image IDs to file paths

## Notes

- First run will download the CLIP model (~600MB)
- Indexing time depends on number of images (approximately 1-2 seconds per image on CPU)
- The application runs entirely on CPU (no GPU required)
- Corrupt or unreadable images are skipped during indexing
- Re-indexing overwrites the previous index

## Troubleshooting

**Model download issues**: Ensure you have internet connection for the first run (model download)

**Memory errors**: If indexing fails with memory errors, try indexing a smaller subset of images

**Path errors**: Use absolute paths or paths relative to the application directory

## License

This application uses:
- CLIP by OpenAI (MIT License)
- FAISS by Facebook Research (MIT License)
- Streamlit (Apache 2.0 License)
