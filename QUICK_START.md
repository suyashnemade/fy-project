# Quick Start Guide - Building and Running the App

## Step 1: Install Dependencies

Make sure all required packages are installed:
```bash
pip install -r requirements.txt
```

This will install:
- PyTorch and dependencies
- CLIP model
- FAISS
- CustomTkinter
- PyInstaller

## Step 2: Build the Application

### Windows:
```bash
build_app.bat
```

Or manually:
```bash
python -m PyInstaller desktop_app.spec
```

### Linux/Mac:
```bash
chmod +x build_app.sh
./build_app.sh
```

Or manually:
```bash
python -m PyInstaller desktop_app.spec
```

## Step 3: Run the Application

After building, the executable will be in the `dist` folder:

**Windows:**
- Double-click `dist\SemanticImageSearch.exe`
- Or run from command line: `dist\SemanticImageSearch.exe`

**Linux/Mac:**
- Run: `./dist/SemanticImageSearch`

## First Launch

1. The app will load the CLIP model (first time may take a minute)
2. Click "Browse" in the sidebar to select an image directory
3. Click "Index Images" to build the search index
4. Wait for indexing to complete
5. Enter a search query and click "Search"

## Troubleshooting

- **Large executable size**: Normal (~1-2GB) due to PyTorch/CLIP dependencies
- **First run slow**: CLIP model downloads on first launch
- **Storage folder**: Created automatically next to the executable

For detailed build instructions, see `BUILD_INSTRUCTIONS.md`
