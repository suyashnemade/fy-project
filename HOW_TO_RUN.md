# Project Run Guide

Follow these steps to run the Semantic Image and Video Search project on a new computer.

### Prerequisites

- **Python**: Version 3.9 or higher.
- **Node.js**: Version 16 or higher.
- **Git**: (Optional) Required if you want to clone the repository.

---

### Step 0: Download the Latest Version from GitHub

Before you begin, you can pull the most up-to-date code directly from GitHub. 
Find the updated version of the project at the link below:

**GitHub Link:** [https://github.com/suyashnemade/seekr](https://github.com/suyashnemade/seekr)

To download the project, execute this in your terminal:
```bash
git clone https://github.com/suyashnemade/seekr.git
cd seekr
```
*(If you already have the project extracted from a zip or CD, you can skip this step).*

---
### Step 1: Set Up the Python Backend

1. **Open a terminal** in the root directory of the project.
2. **Create a virtual environment** to isolate dependencies:
   ```bash
   python -m venv run_env
   ```
3. **Activate the environment**:
   - **Windows:** 
     ```bash
     .\run_env\Scripts\activate
     ```
   - **Mac/Linux:** 
     ```bash
     source run_env/bin/activate
     ```
4. **Install backend dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: This might take a few minutes as PyTorch and torchvision are large packages).*
5. **Start the API Server**:
   ```bash
   python run_api.py
   ```
   *(Keep this terminal open. The backend handles image processing, video indexing, and search capabilities).*

---

### Step 2: Run the Frontend (Desktop or Web)

1. **Open a second terminal window**.
2. **Navigate to the frontend directory**:
   ```bash
   cd newui
   ```
3. **Install the Node dependencies**:
   ```bash
   npm install
   ```

**Option A: Run as a Desktop App (Recommended)**
To launch the native Tauri desktop interface, run:
```bash
npm run tauri dev
```
*(Tauri will automatically connect to your running Python API backend on Port 8000).*

**Option B: Run as a Web App**
If you prefer to run it in a standard web browser, start the Vite server:
```bash
npm run dev
```
Then, **open your browser** and navigate to the URL provided (usually `http://localhost:5173`).

---

### Optional: Build a Standalone Executable (With Bundled Backend)

To package this application as a final standalone executable (so it can run just by double-clicking, without needing open terminals):
1. Ensure the Python backend has successfully compiled via `build_backend.ps1`.
2. Inside the `newui` folder, build the Tauri app:
   ```bash
   npm run tauri build
   ```
   This will output the final `.exe` application to `newui/src-tauri/target/release/`.
