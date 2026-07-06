# Project Requirements Document (PRD)
## AI-Based Image Difference Detection, Visualization, and Automated Change Summarization

### 1. Objective
To design and implement an AI-powered image comparison system that accepts two drawings (or PDF files), detects and localizes visual differences, produces an annotated comparison visualization, computes change metrics, and generates a natural language summary explaining the differences.

---

### 2. Functional Requirements

#### FR-1: Image Upload
- **Supported Formats**: JPG, JPEG, PNG, and PDF files.
- **Validation**: Validate that files exist, are readable, and contain static images/sheets before initiating analysis.
- **PDF Conversion**: Converts PDF files into high-resolution image matrices using PyMuPDF (`fitz`) at a standard layout density of 150 DPI.

#### FR-2: Image Preprocessing & Alignment
- **Resizing**: Resize the comparison image (B) to match the reference image (A) dimensions.
- **Registration**: Align the drawings using Oriented FAST and Rotated BRIEF (ORB) keypoint detection and Hamming distance matching. Compute homography projection via RANSAC to resolve rotation, scaling, and translation offsets.
- **Normalization**: Clean contrast/brightness to prevent scanning noise from impacting difference analysis.

#### FR-3: Difference Detection
- **Algorithm**: Compute structural differences using the Structural Similarity Index (SSIM) and pixel-wise absolute difference subtraction (`cv2.absdiff`).
- **Noise Filtering**: Apply morphological closing/opening filters to eliminate minor pixel noise (e.g., scanner artifacts) and merge nearby structural changes.

#### FR-4: Difference Visualization
- **Annotated Visuals**: Highlight changed regions with red bounding boxes on both reference and comparison drawings.
- **CAD Difference Map**: Render a customized, color-coded change map:
  - **Red**: Removed elements (Reference only).
  - **Green**: Added elements (Comparison only).
  - **Blue-Cyan**: Modified, shifted, or scaled drawings.
  - **Light Gray**: Unchanged linework on white background.
- **Side-by-Side View**: Merge annotated drawings into a single double-wide panel.
- **Blend Overlay**: Create a 50% opacity cross-dissolve blend between aligned sheets.

#### FR-5: Difference Statistics
- **Contour Extraction**: Count individual modified regions.
- **Change Metrics**: Calculate total modified area (in pixels) and percentage changed relative to the drawing dimensions.
- **Geometry Mapping**: Extract bounding boxes `[x, y, w, h]` and layout coordinates (e.g. `top-left`, `bottom-center`).

#### FR-6: AI-Based Change Summary & Reports
- **Natural Language Summary**: Formulates metrics, locations, and severities into a technical summary paragraph using the Gemini API.
- **Printable Report**: Exposes a printable HTML comparison report featuring metrics, AI summaries, difference drawings, and a detailed change log. Optimizes elements with print stylesheets to download directly to a PDF document.
