# PowerShell Script to bundle the python backend and place it for Tauri

Write-Host "Building Python Backend with PyInstaller... (This may take roughly 5-15 minutes due to PyTorch)"

# Clean previous builds
if (Test-Path -Path "./build") { Remove-Item -Path "./build" -Recurse -Force }
if (Test-Path -Path "./dist") { Remove-Item -Path "./dist" -Recurse -Force }
if (Test-Path -Path "./run_api.spec") { Remove-Item -Path "./run_api.spec" -Force }

# Make sure binaries directory exists
$TauriBinDir = ".\newui\src-tauri\binaries"
if (-Not (Test-Path -Path $TauriBinDir)) {
    New-Item -ItemType Directory -Force -Path $TauriBinDir | Out-Null
}

# Run PyInstaller
# We use --onefile. Warning: --onefile makes the startup slower as it extracts itself every time it boots. 
# --onedir is faster to start, but onefile is required by default Tauri externalBin unless custom configuring.
pyinstaller --name "newuiapi-sidecar" --onefile run_api.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Build successful. Moving executable to Tauri bundle folder..." -ForegroundColor Green

# Tauri architecture target strings
$TargetExe = "$TauriBinDir\newuiapi-sidecar-x86_64-pc-windows-msvc.exe"

# Copy the file
Copy-Item ".\dist\newuiapi-sidecar.exe" -Destination $TargetExe -Force

Write-Host "Done! The Python Sidecar is ready at $TargetExe" -ForegroundColor Cyan
Write-Host "You can now run 'npm run tauri build' in the newui folder." -ForegroundColor Cyan
