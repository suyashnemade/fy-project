# Building the Desktop Application with PyInstaller

This guide explains how to package the Semantic Image Search desktop application into a standalone executable using PyInstaller.

## Prerequisites

1. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure PyInstaller is installed (already included in requirements.txt):
   ```bash
   pip install pyinstaller>=6.10.0
   ```

## Building the Application

### Windows

**Option 1: Using the build script (Recommended)**
```bash
build_app.bat
```

**Option 2: Manual build**
```bash
python -m PyInstaller desktop_app.spec
```

### Linux/Mac

**Option 1: Using the build script**
```bash
chmod +x build_app.sh
./build_app.sh
```

**Option 2: Manual build**
```bash
python -m PyInstaller desktop_app.spec
```

## Build Output

After building, the executable will be located in:
- **Windows**: `dist\SemanticImageSearch.exe`
- **Linux/Mac**: `dist/SemanticImageSearch`

## Running the Application

### From Build Directory

Simply double-click the executable or run from command line:
- **Windows**: `dist\SemanticImageSearch.exe`
- **Linux/Mac**: `./dist/SemanticImageSearch`

### Important Notes

1. **Storage Directory**: The app will create a `storage` folder in the same directory as the executable to store:
   - FAISS index (`faiss.index`)
   - Embeddings (`embeddings.npy`)
   - Metadata (`metadata.json`)

2. **First Run**: On first launch, the CLIP model will be downloaded (~1GB) if not already cached in the user's home directory.

3. **File Size**: The executable will be large (~1-2GB) due to PyTorch, CLIP, and FAISS dependencies.

4. **Distribution**: If distributing the app, you may want to:
   - Compress the `dist` folder into a ZIP file
   - Include a README with instructions
   - Note the storage directory location

## Troubleshooting

### Build Errors

If you encounter import errors during build:
1. Make sure all dependencies are installed
2. Try building with `--debug=all` to see detailed error messages:
   ```bash
   python -m PyInstaller desktop_app.spec --debug=all
   ```

### Runtime Errors

If the app crashes on launch:
1. Try running with console enabled (edit `desktop_app.spec` and set `console=True`)
2. Check that all required files are included in the build
3. Verify the storage directory can be created/written to

### Missing Dependencies

If you get "module not found" errors:
1. Add the missing module to `hiddenimports` in `desktop_app.spec`
2. Rebuild the application

## Advanced: One-Folder Build

If you prefer a one-folder build (easier to debug), modify `desktop_app.spec`:

Change the `EXE` section to use `COLLECT` instead:

```python
exe = EXE(...)  # Keep as is but set name to 'desktop_app'

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SemanticImageSearch'
)
```

This creates a folder with all dependencies, making it easier to see what's included.

## File Structure After Build

```
imageproject/
├── dist/
│   └── SemanticImageSearch.exe  (or SemanticImageSearch on Linux/Mac)
├── build/                        (temporary build files, can be deleted)
├── desktop_app.spec             (PyInstaller spec file)
└── ...
```

## Icon (Optional)

To add a custom icon to your executable:
1. Create or download an `.ico` file (Windows) or `.icns` file (Mac)
2. Update `desktop_app.spec`:
   ```python
   icon='path/to/your/icon.ico'
   ```
3. Rebuild the application
