#!/bin/bash

echo "Building Semantic Image Search Desktop Application..."
echo

# Check if PyInstaller is installed
if ! python -m pip show pyinstaller > /dev/null 2>&1; then
    echo "PyInstaller not found. Installing..."
    python -m pip install pyinstaller
fi

echo
echo "Cleaning previous builds..."
rm -rf build dist

echo
echo "Building application with PyInstaller..."
python -m PyInstaller desktop_app.spec

echo
if [ -f "dist/SemanticImageSearch" ] || [ -f "dist/SemanticImageSearch.exe" ]; then
    echo "Build successful!"
    echo
    echo "Executable location: dist/SemanticImageSearch (or .exe on Windows)"
    echo
    echo "You can now run the application from the dist directory."
else
    echo "Build failed. Please check the error messages above."
fi
