# CAD Diff AI: Engineering Drawing Comparison & Change Summarizer

An AI-powered web application designed to automatically detect, align, and highlight visual changes between two engineering drawings, blueprints, or documents. The system calculates geometric statistics of the modifications and generates a natural language change summary using computer vision and generative AI.

---

## Features

- **Document Preprocessing**: Support for multi-page **PDF files**, JPEG, and PNG images. Automatic page conversion via PyMuPDF.
- **Image Registration & Alignment**: High-accuracy alignment using Oriented FAST and Rotated BRIEF (**ORB**) feature keypoint matching and **RANSAC Homography** to correct scaling, rotation, or scanning translations.
- **Hybrid Difference Detection**: Detects both structural modifications and fine line-work edits using a combined **Structural Similarity (SSIM)** index and absolute pixel differences.
- **Standard CAD Difference Map**: Renders differences color-coded to engineering versioning standards:
  - **Red**: Removed line-work (only in Reference sheet).
  - **Green**: Added line-work (new in Comparison sheet).
  - **Blue-Cyan**: Modified, shifted, or scaled drawings.
  - **Light Gray**: Unchanged background elements.
- **Difference Statistics**: Contour extraction detailing bounding box coordinates, areas, severity labels, and 3x3 layout grid placement coordinates (e.g., `bottom-center`, `top-left`).
- **AI-Generated Change Summaries**: Consolidates layout locations, areas, and severities into a technical summary paragraph using the Gemini API. Includes a smart rule-based fallback when offline or without an API key.
- **High-Fidelity Dashboard UI**:
  - Drag-and-drop file uploaders.
  - KPI panels displaying total modifications, change percentage, SSIM similarity, and alignment status.
  - Interactive Preview Canvas with multiple viewer modes: **Difference Map**, **Interactive Split Slider**, **Transparency Blend**, and original sheets.
  - Actionable change table allowing users to click a detected contour to trace it.

---

## System Architecture

```
                                 +------------------------------+
                                 |       React SPA UI           |
                                 +--------------+---------------+
                                                |  (API calls)
                                                v
                                 +--------------+---------------+
                                 |       FastAPI Server         |
                                 +--------------+---------------+
                                                |
         +------------------+-------------------+-------------------+------------------+
         |                  |                   |                   |                  |
         v                  v                   v                   v                  v
+--------+-------+  +-------+--------+  +-------+--------+  +-------+--------+  +------+-------+
|  preprocess.py |  |   compare.py   |  |  statistics.py |  |  visualize.py  |  |  summary.py  |
+--------+-------+  +-------+--------+  +-------+--------+  +-------+--------+  +------+-------+
| PDF conversion |  | SSIM map       |  | Contours       |  | BBoxes         |  | Gemini API   |
| ORB Align      |  | absdiff        |  | Centroids      |  | Standard Map   |  | Heuristic    |
| Homography     |  | Morphology     |  | Grid Layout    |  | Transparency   |  | Fallback     |
+----------------+  +----------------+  +----------------+  +----------------+  +--------------+
```

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, OpenCV, PyMuPDF, Scikit-Image, Google GenAI
- **Frontend**: React 18, Vite, Vanilla CSS (Dark theme design tokens), Lucide Icons

---

## Prerequisites

- **Python 3.10+**
- **Node.js v18+** & **npm**

---

## Getting Started

### 1. Setup the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env` (optional, for AI summaries):
   Create/edit the `.env` file and insert your Gemini API Key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
5. Start the backend development server:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   The backend will be running at `http://localhost:8000`.

### 2. Setup the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the frontend Vite server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser to view the application.

---

## Running Integration Tests

To verify the CV processing and alignment pipeline locally without running the web servers, we have created a test suite script that programmatically generates shifted drawings and compares them:

1. Navigate to `backend/` and run the script:
   ```bash
   .venv\Scripts\python.exe test_pipeline.py
   ```
2. The script will:
   - Generate two drawings in `samples/` (`drawing_v1.png` and a shifted/edited `drawing_v2.png`).
   - Run the homography alignment (RANSAC).
   - Detect the changes (SSIM).
   - Extract metrics and write results to the terminal.
   - Save output visualization files inside `samples/`.

---

## Sample Deliverables

Pre-generated test drawings and comparison outputs are available under the `/samples` folder in the root directory:
- `drawing_v1.png`: Reference Version 1.0.
- `drawing_v2.png`: Comparison Version 1.1 (containing translation offset and manual deletions/additions).
- `test_run_color_diff.png`: The processed Red/Green comparison sheet.
- `test_run_side_by_side.png`: Bounding box highlight stitch.