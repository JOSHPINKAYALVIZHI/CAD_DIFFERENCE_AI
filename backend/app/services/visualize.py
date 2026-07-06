import cv2
import numpy as np
import os
from app.core.config import settings

def draw_annotations(
    img: np.ndarray,
    regions: list[dict],
    color: tuple[int, int, int] = (0, 0, 255),
    thickness: int = 2
) -> np.ndarray:
    """
    Draws bounding boxes and labels for each difference region on a copy of the image.
    """
    annotated = img.copy()
    for r in regions:
        x, y, w, h = r["bbox"]
        rid = r["id"]
        
        # Draw bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)
        
        # Draw label background
        label = f"#{rid} ({r['severity']})"
        (lbl_w, lbl_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.rectangle(
            annotated, 
            (x, y - lbl_h - 4), 
            (x + lbl_w + 4, y), 
            color, 
            -1
        )
        # Write text label in white
        cv2.putText(
            annotated, 
            label, 
            (x + 2, y - 2), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.4, 
            (255, 255, 255), 
            1, 
            cv2.LINE_AA
        )
    return annotated

def generate_color_diff(
    ref_img: np.ndarray,
    cmp_img: np.ndarray,
    mask: np.ndarray
) -> np.ndarray:
    """
    Renders a color-coded representation of differences:
    - Identical background is rendered as faded gray lines on a white canvas.
    - Removed content (Reference only) is colored Red.
    - Added content (Comparison only) is colored Green.
    - Modified/Shifted content is colored Blue.
    """
    h, w = ref_img.shape[:2]
    color_diff = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    gray_cmp = cv2.cvtColor(cmp_img, cv2.COLOR_BGR2GRAY)
    
    # Identical content (where mask is 0)
    matched_mask = (mask == 0)
    
    # Draw drawing lines as faded gray
    ink_mask = (gray_ref < 210) & matched_mask
    color_diff[ink_mask] = [180, 180, 180]  # Light Gray (BGR)
    
    # Difference content (where mask is 255)
    diff_mask = (mask == 255)
    
    # Removed content: dark in Ref, light in Cmp
    removed_mask = diff_mask & (gray_ref < 210) & (gray_cmp >= 210)
    color_diff[removed_mask] = [0, 0, 240]  # Soft Red
    
    # Added content: light in Ref, dark in Cmp
    added_mask = diff_mask & (gray_ref >= 210) & (gray_cmp < 210)
    color_diff[added_mask] = [0, 180, 0]  # Soft Green
    
    # Modified/Shifted content: different but doesn't fit simple add/remove
    mod_mask = diff_mask & ~(removed_mask | added_mask)
    color_diff[mod_mask] = [220, 100, 0]  # Blue-Cyan (BGR)
    
    return color_diff

def generate_blend_overlay(
    ref_img: np.ndarray,
    cmp_img: np.ndarray,
    alpha: float = 0.5
) -> np.ndarray:
    """
    Creates a blended image by overlaying ref_img and cmp_img with transparency.
    """
    return cv2.addWeighted(ref_img, alpha, cmp_img, 1.0 - alpha, 0.0)

def save_visualizations(
    ref_img: np.ndarray,
    cmp_img: np.ndarray,
    mask: np.ndarray,
    regions: list[dict],
    session_id: str
) -> dict:
    """
    Generates all requested visualizations and saves them to the outputs directory.
    Returns relative URLs for access.
    """
    # Crop borders from saved output images to keep only the active drawing area
    h, w = ref_img.shape[:2]
    margin_h = int(h * 0.04)
    margin_w = int(w * 0.04)
    
    crop_ref_img = ref_img[margin_h:h-margin_h, margin_w:w-margin_w]
    crop_cmp_img = cmp_img[margin_h:h-margin_h, margin_w:w-margin_w]
    crop_mask = mask[margin_h:h-margin_h, margin_w:w-margin_w]
    
    # Shift coordinate spaces for drawing annotations on the cropped layout
    shifted_regions = []
    for r in regions:
        rx, ry, rw, rh = r["bbox"]
        shifted_regions.append({
            **r,
            "bbox": [rx - margin_w, ry - margin_h, rw, rh]
        })
        
    # 1. Generate annotated original images with bounding boxes (on cropped drawings)
    annotated_ref = draw_annotations(crop_ref_img, shifted_regions, color=(0, 0, 255))
    annotated_cmp = draw_annotations(crop_cmp_img, shifted_regions, color=(0, 0, 255))
    
    # 2. Generate side-by-side comparison
    h_ref, w_ref = annotated_ref.shape[:2]
    h_cmp, w_cmp = annotated_cmp.shape[:2]
    
    # Make sure they have identical heights for side-by-side alignment
    if h_ref != h_cmp:
        annotated_cmp = cv2.resize(annotated_cmp, (w_cmp, h_ref))
    
    side_by_side = np.hstack((annotated_ref, annotated_cmp))
    
    # 3. Generate color difference map (on cropped drawings)
    color_diff = generate_color_diff(crop_ref_img, crop_cmp_img, crop_mask)
    
    # 4. Generate blend overlay
    blend_overlay = generate_blend_overlay(crop_ref_img, crop_cmp_img, alpha=0.5)
    
    # Save files to settings.OUTPUT_DIR
    paths = {}
    filenames = {
        "annotated_ref": f"{session_id}_annotated_ref.png",
        "annotated_cmp": f"{session_id}_annotated_cmp.png",
        "side_by_side": f"{session_id}_side_by_side.png",
        "color_diff": f"{session_id}_color_diff.png",
        "blend_overlay": f"{session_id}_blend.png",
        "mask": f"{session_id}_mask.png"
    }
    
    # Save the files
    cv2.imwrite(os.path.join(settings.OUTPUT_DIR, filenames["annotated_ref"]), annotated_ref)
    cv2.imwrite(os.path.join(settings.OUTPUT_DIR, filenames["annotated_cmp"]), annotated_cmp)
    cv2.imwrite(os.path.join(settings.OUTPUT_DIR, filenames["side_by_side"]), side_by_side)
    cv2.imwrite(os.path.join(settings.OUTPUT_DIR, filenames["color_diff"]), color_diff)
    cv2.imwrite(os.path.join(settings.OUTPUT_DIR, filenames["blend_overlay"]), blend_overlay)
    cv2.imwrite(os.path.join(settings.OUTPUT_DIR, filenames["mask"]), mask)
    
    # 5. Extract and save cropped region details (Before/After context previews)
    for r in regions:
        x, y, w, h = r["bbox"]
        rid = r["id"]
        
        # Add 15px padding for visual context
        h_max, w_max = ref_img.shape[:2]
        x1 = max(0, x - 15)
        y1 = max(0, y - 15)
        x2 = min(w_max, x + w + 15)
        y2 = min(h_max, y + h + 15)
        
        crop_ref = ref_img[y1:y2, x1:x2]
        crop_cmp = cmp_img[y1:y2, x1:x2]
        
        crop_ref_name = f"{session_id}_region_{rid}_ref.png"
        crop_cmp_name = f"{session_id}_region_{rid}_cmp.png"
        
        cv2.imwrite(os.path.join(settings.OUTPUT_DIR, crop_ref_name), crop_ref)
        cv2.imwrite(os.path.join(settings.OUTPUT_DIR, crop_cmp_name), crop_cmp)
        
        # Attach URLs to the region dictionary
        r["crop_ref_url"] = f"/api/v1/outputs/{crop_ref_name}"
        r["crop_cmp_url"] = f"/api/v1/outputs/{crop_cmp_name}"
        
    # Construct relative server URLs
    return {k: f"/api/v1/outputs/{v}" for k, v in filenames.items()}

