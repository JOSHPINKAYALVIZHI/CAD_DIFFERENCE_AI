from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import HTMLResponse
import uuid
import os
import shutil
import json
from app.core.config import settings
from app.schemas.response import ComparisonResponse
from app.services.preprocess import preprocess_and_load, align_images, crop_and_normalize_pair
from app.services.compare import detect_differences, estimate_optimal_noise_limit
from app.services.statistics import calculate_statistics
from app.services.visualize import save_visualizations
from app.services.summary import generate_ai_summary

router = APIRouter(prefix="/api/v1", tags=["Image Comparison"])

@router.post("/compare", response_model=ComparisonResponse)
async def compare_images(
    image_a: UploadFile = File(...),
    image_b: UploadFile = File(...),
    min_area: int = Query(default=0, description="Minimum contour area in pixels to identify as difference. Set to 0 to auto-detect.")
):
    session_id = str(uuid.uuid4())
    
    # Extract file extensions
    ext_a = os.path.splitext(image_a.filename)[1]
    ext_b = os.path.splitext(image_b.filename)[1]
    
    # Define save paths
    path_a = os.path.join(settings.UPLOAD_DIR, f"{session_id}_ref{ext_a}")
    path_b = os.path.join(settings.UPLOAD_DIR, f"{session_id}_cmp{ext_b}")
    
    try:
        # Save uploads to files
        with open(path_a, "wb") as buffer_a:
            shutil.copyfileobj(image_a.file, buffer_a)
        with open(path_b, "wb") as buffer_b:
            shutil.copyfileobj(image_b.file, buffer_b)
            
        # 1. Preprocess inputs (loading and PDF rasterization if needed)
        img_a = preprocess_and_load(path_a)
        img_b = preprocess_and_load(path_b)
        
        # Crop empty margins jointly and normalize resolution for scale stability
        img_a, img_b = crop_and_normalize_pair(img_a, img_b)
        
        # 2. Image Registration / Alignment (ORB & Homography)
        aligned_b, aligned_success = align_images(img_a, img_b)
        
        # 3. Difference Detection (SSIM & absdiff)
        mask, similarity_score = detect_differences(img_a, aligned_b)
        
        # Auto-detect optimal noise limit if min_area is 0 or less
        if min_area <= 0:
            min_area = estimate_optimal_noise_limit(mask)
            
        # 4. Extract Statistics & Layout centroids
        stats = calculate_statistics(mask, min_area=min_area)
        stats["detected_noise_limit"] = min_area
        
        # 5. Render and Save Visualizations
        viz_urls = save_visualizations(
            ref_img=img_a,
            cmp_img=aligned_b,
            mask=mask,
            regions=stats["regions"],
            session_id=session_id
        )
        
        # 6. Generate AI Change Summary
        summary = generate_ai_summary(stats)
        
        # Save metadata for report generation
        report_data = {
            "session_id": session_id,
            "similarity_score": float(similarity_score),
            "statistics": stats,
            "summary": summary,
            "visualizations": viz_urls
        }
        report_path = os.path.join(settings.OUTPUT_DIR, f"{session_id}_report.json")
        with open(report_path, "w") as rf:
            json.dump(report_data, rf, indent=2)
            
        return ComparisonResponse(
            session_id=session_id,
            status="success" if aligned_success else "fallback_unaligned",
            similarity_score=similarity_score,
            statistics=stats,
            summary=summary,
            visualizations=viz_urls
        )
        
    except Exception as e:
        # Log detail for debugging
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred during comparison pipeline: {str(e)}"
        )

@router.get("/compare/{session_id}/report", response_class=HTMLResponse)
async def generate_report_html(session_id: str):
    from datetime import datetime
    report_path = os.path.join(settings.OUTPUT_DIR, f"{session_id}_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Comparison report metadata not found.")
        
    with open(report_path, "r") as rf:
        data = json.load(rf)
        
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAD Drawing Comparison Report - {session_id[:8]}</title>
    <style>
        body {{
            font-family: 'Outfit', 'Segoe UI', Arial, sans-serif;
            color: #1e293b;
            max-width: 1100px;
            margin: 0 auto;
            padding: 30px;
            background: #f8fafc;
            line-height: 1.5;
        }}
        .no-print-bar {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 12px 24px;
            border-radius: 8px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }}
        .btn {{
            background: #2563eb;
            color: #ffffff;
            border: none;
            padding: 8px 18px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.15s;
        }}
        .btn:hover {{
            background: #1d4ed8;
        }}
        .report-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 25px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.025em;
            color: #0f172a;
            margin: 0;
        }}
        .subtitle {{
            font-size: 0.85rem;
            color: #64748b;
            margin-top: 6px;
            font-family: monospace;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 18px;
            text-align: center;
            background: #f8fafc;
        }}
        .stat-val {{
            font-size: 28px;
            font-weight: 800;
            color: #2563eb;
            line-height: 1;
        }}
        .stat-lbl {{
            font-size: 11px;
            color: #64748b;
            margin-top: 6px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
        }}
        .summary-container {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 24px;
            margin-bottom: 35px;
        }}
        @media (max-width: 768px) {{
            .summary-container {{
                grid-template-columns: 1fr;
            }}
        }}
        .summary-box {{
            background: #eff6ff;
            border-left: 4px solid #2563eb;
            padding: 20px;
            border-radius: 0 8px 8px 0;
            font-size: 0.95rem;
            color: #1e3a8a;
        }}
        .summary-title {{
            font-weight: 700;
            color: #1e3a8a;
            margin-bottom: 8px;
            font-size: 1.05rem;
        }}
        .legend-box {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 16px;
            border-radius: 8px;
        }}
        .legend-title {{
            font-size: 0.85rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            margin-bottom: 6px;
            color: #475569;
        }}
        .legend-item:last-child {{
            margin-bottom: 0;
        }}
        .color-pill {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
            display: inline-block;
        }}
        .pill-removed {{ background: #dc2626; }}
        .pill-added {{ background: #059669; }}
        .pill-modified {{ background: #2563eb; }}
        .pill-unchanged {{ background: #cbd5e1; }}
        
        .section-title {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 8px;
            margin-bottom: 20px;
            margin-top: 35px;
        }}
        .image-wrapper {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .report-img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            text-align: left;
            font-size: 0.85rem;
        }}
        th {{
            background: #f8fafc;
            font-weight: 600;
            color: #475569;
        }}
        .badge {{
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        .badge-low {{ background: #d1fae5; color: #065f46; border: 1px solid rgba(6,95,70,0.2); }}
        .badge-medium {{ background: #fef3c7; color: #92400e; border: 1px solid rgba(146,64,14,0.2); }}
        .badge-high {{ background: #fee2e2; color: #991b1b; border: 1px solid rgba(153,27,27,0.2); }}
        
        @media print {{
            body {{ padding: 0; background: #ffffff; }}
            .no-print-bar {{ display: none !important; }}
            .report-card {{ border: none; padding: 0; box-shadow: none; }}
            .page-break {{ page-break-before: always; }}
        }}
    </style>
</head>
<body>
    <div class="no-print-bar">
        <span style="font-size: 0.9rem; color: #475569; font-weight: 500;">Drawing border frame template lines have been filtered out from the analysis.</span>
        <button class="btn" onclick="window.print()">Download PDF Report</button>
    </div>
    
    <div class="report-card">
        <div class="header">
            <h1 class="title">CAD DRAWING COMPARISON REPORT</h1>
            <div class="subtitle" style="margin-top: 6px; font-size: 0.8rem; color: #64748b; font-family: inherit;">Generated: {current_time} &nbsp;|&nbsp; Session: {session_id}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val">{data['statistics']['total_regions']}</div>
                <div class="stat-lbl">Identified Modifications</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{data['statistics']['change_percentage']}%</div>
                <div class="stat-lbl">Percentage Changed Area</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{(data['similarity_score'] * 100):.1f}%</div>
                <div class="stat-lbl">Drawing Similarity</div>
            </div>
        </div>

        <div class="summary-container">
            <div class="summary-box">
                <div class="summary-title">AI Change Summary</div>
                <div>{data['summary']}</div>
            </div>
            
            <div class="legend-box">
                <div class="legend-title">Color Code Key</div>
                <div class="legend-item">
                    <span class="color-pill pill-removed"></span>
                    <span>Removed details (A only)</span>
                </div>
                <div class="legend-item">
                    <span class="color-pill pill-added"></span>
                    <span>New additions (B only)</span>
                </div>
                <div class="legend-item">
                    <span class="color-pill pill-modified"></span>
                    <span>Modified linework details</span>
                </div>
                <div class="legend-item">
                    <span class="color-pill pill-unchanged"></span>
                    <span>Unchanged drawing blueprint</span>
                </div>
            </div>
        </div>

        <div class="section-title">Color-Coded Difference Map</div>
        <div class="image-wrapper">
            <img class="report-img" src="/api/v1/outputs/{session_id}_color_diff.png" alt="Color Difference Map">
        </div>

        <div class="section-title page-break">Side-by-Side Bounding Box Highlights</div>
        <div class="image-wrapper">
            <img class="report-img" src="/api/v1/outputs/{session_id}_side_by_side.png" alt="Side by Side BBoxes">
        </div>

        <div class="section-title">Detailed Modifications Registry</div>
        <p style="font-size: 0.8rem; color: #64748b; margin-top: -10px; margin-bottom: 15px;">
            The registry details individual modification zones located by the contour logic, ordered by area size. Bounding boxes are defined in [x, y, width, height] format.
        </p>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Drawing Quadrant Location</th>
                    <th>Severity Scale</th>
                    <th>Modified Area Size</th>
                    <th>Coordinates Bounds [x, y, w, h]</th>
                    <th>Visual Crop Comparison (Before vs After)</th>
                </tr>
            </thead>
            <tbody>
"""
    for r in data['statistics']['regions']:
        badge_cls = f"badge badge-{r['severity']}"
        # format location name professionally
        location_name = r['location'].replace('top', 'Upper').replace('bottom', 'Lower').replace('middle', 'Center').replace('-', ' ')
        
        # Crop visuals column
        crop_html = ""
        ref_url = r.get("crop_ref_url")
        cmp_url = r.get("crop_cmp_url")
        if ref_url and cmp_url:
            crop_html = f"""
            <div style="display: flex; gap: 12px; align-items: center;">
                <div style="text-align: center;">
                    <div style="font-size: 0.65rem; color: #64748b; margin-bottom: 2px;">Ref (A)</div>
                    <img src="{ref_url}" style="max-height: 80px; max-width: 140px; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; display: block;" />
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.65rem; color: #64748b; margin-bottom: 2px;">Comp (B)</div>
                    <img src="{cmp_url}" style="max-height: 80px; max-width: 140px; border: 1px solid #cbd5e1; border-radius: 4px; background: #ffffff; display: block;" />
                </div>
            </div>
            """
        else:
            crop_html = '<span style="color:#94a3b8; font-size:0.75rem;">N/A</span>'

        html_content += f"""                <tr>
                    <td style="font-weight: 700; color: #2563eb;">#{r['id']}</td>
                    <td style="text-transform: capitalize; font-weight: 500;">{location_name}</td>
                    <td><span class="{badge_cls}">{r['severity']}</span></td>
                    <td>{int(r['area']):,} px²</td>
                    <td style="font-family: monospace; color: #475569; font-size: 0.8rem;">[{', '.join(map(str, r['bbox']))}]</td>
                    <td>{crop_html}</td>
                </tr>
"""
    html_content += """            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content, status_code=200)


# --- Chatbot schemas & endpoint ---
from pydantic import BaseModel
from typing import List
from app.services.chat import generate_chat_response

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str

@router.post("/compare/{session_id}/chat", response_model=ChatResponse)
async def chat_about_comparison(
    session_id: str,
    request: ChatRequest
):
    # 1. Load the session report JSON file
    report_path = os.path.join(settings.OUTPUT_DIR, f"{session_id}_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Session report not found. Please compare drawings first.")
        
    try:
        with open(report_path, "r") as f:
            report_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read report data: {str(e)}")
        
    # 2. Call the chat helper service
    try:
        history_list = [{"role": msg.role, "content": msg.content} for msg in request.history]
        response_text = generate_chat_response(report_data, request.message, history_list)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chatbot response: {str(e)}")