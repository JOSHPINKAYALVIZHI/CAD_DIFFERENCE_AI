import os
import json

# Force mock config before import
os.environ["UPLOAD_DIR"] = "app/uploads"
os.environ["OUTPUT_DIR"] = "app/outputs"

from app.services.preprocess import preprocess_and_load, align_images, crop_and_normalize_pair
from app.services.compare import detect_differences
from app.services.statistics import calculate_statistics
from app.services.visualize import save_visualizations
from app.services.summary import generate_ai_summary

def run_test():
    print("=== STARTING CAD DIFFERENCE PIPELINE TEST ===")
    
    # 1. Load files
    print("\n[Step 1] Loading sample drawings...")
    ref = preprocess_and_load("samples/drawing_v1.png")
    cmp = preprocess_and_load("samples/drawing_v2.png")
    
    # Crop empty margins jointly and normalize resolution
    ref, cmp = crop_and_normalize_pair(ref, cmp)
    
    print(f"Reference shape: {ref.shape}")
    print(f"Comparison shape: {cmp.shape}")
    
    # 2. Alignment
    print("\n[Step 2] Aligning drawings using ORB homography...")
    aligned, success = align_images(ref, cmp)
    print(f"Alignment Success Flag: {success}")
    
    # 3. Differences
    print("\n[Step 3] Computing Structural Similarity difference mask...")
    mask, score = detect_differences(ref, aligned)
    print(f"SSIM Score: {score:.4f}")
    
    # 4. Statistics
    print("\n[Step 4] Extracting changed region statistics...")
    stats = calculate_statistics(mask, min_area=30)
    print(f"Total Change Contours: {stats['total_regions']}")
    print(f"Total Modified Area: {stats['total_changed_area_px']} px²")
    print(f"Modified Area Ratio: {stats['change_percentage']}%")
    for r in stats["regions"]:
        print(f"  - Region #{r['id']}: Size={r['area']}px², Place={r['location']}, Severity={r['severity']}, BBox={r['bbox']}")
        
    # 5. Visualizations
    print("\n[Step 5] Creating visualizations and file links...")
    viz = save_visualizations(ref, aligned, mask, stats["regions"], "test_run")
    print(f"Visualizations: {json.dumps(viz, indent=2)}")
    
    # 6. Change Summary
    print("\n[Step 6] Compiling summary (AI or Fallback)...")
    summary = generate_ai_summary(stats)
    print(f"Summary text:\n{summary}")
    
    print("\n=== PIPELINE TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_test()
