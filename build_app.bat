@echo off
echo Building Semantic Image Search Desktop Application...
echo.

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
)

echo.
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building application with PyInstaller...
python -m PyInstaller desktop_app.spec

echo.
if exist dist\SemanticImageSearch.exe (
    echo Build successful!
    echo.
    echo Executable location: dist\SemanticImageSearch.exe
    echo.
    echo You can now run the application by double-clicking the exe file.
) else (
    echo Build failed. Please check the error messages above.
)

pause
