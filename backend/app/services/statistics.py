import cv2
import numpy as np

def get_layout_location(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> str:
    """
    Computes a readable placement descriptor for a region based on its bounding box centroid.
    """
    cx = x + (w // 2)
    cy = y + (h // 2)
    
    # Split layout into 3x3 grids
    # Vertical grid split
    if cy < img_h / 3:
        v_loc = "top"
    elif cy > (2 * img_h) / 3:
        v_loc = "bottom"
    else:
        v_loc = "middle"
        
    # Horizontal grid split
    if cx < img_w / 3:
        h_loc = "left"
    elif cx > (2 * img_w) / 3:
        h_loc = "right"
    else:
        h_loc = "center"
        
    if v_loc == "middle" and h_loc == "center":
        return "center"
    elif v_loc == "middle":
        return f"center-{h_loc}"
    elif h_loc == "center":
        return f"{v_loc}-center"
    else:
        return f"{v_loc}-{h_loc}"

def calculate_statistics(
    mask: np.ndarray,
    min_area: int = 70
) -> dict:
    """
    Analyzes the difference mask, extracts contour statistics, and describes each change.
    Filters out very thin alignment slivers (thickness < 1.4px) and small noise specs.
    """
    img_h, img_w = mask.shape[:2]
    total_area = img_h * img_w
    
    # Find contours in the binary mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    region_id = 1
    total_changed_area = 0.0
    
    for c in contours:
        area = float(cv2.contourArea(c))
        
        # Ignore small regions that are likely noise
        if area < min_area:
            continue
            
        (x, y, w, h) = cv2.boundingRect(c)
        
        # Filter out thin edge slivers (alignment/resampling edge halos)
        max_dim = max(w, h)
        if max_dim > 0:
            thickness = area / max_dim
            if thickness < 1.4 and area < 500:
                continue
                
        cx = int(x + w / 2)
        cy = int(y + h / 2)
        
        # Classify severity of change combining bounding box span (max dimension) and pixel area.
        # Tuned to classify significant architectural/geometric details (e.g. brick patterns, hatches)
        # as High severity.
        max_dim = max(w, h)
        if max_dim >= 35 or area >= 200:
            severity = "high"
        elif max_dim >= 20 or area >= 80:
            severity = "medium"
        else:
            severity = "low"
            
        location = get_layout_location(x, y, w, h, img_w, img_h)
        
        regions.append({
            "id": region_id,
            "bbox": [x, y, w, h],
            "centroid": [cx, cy],
            "area": area,
            "location": location,
            "severity": severity
        })
        
        total_changed_area += area
        region_id += 1
        
    # Sort regions by size (largest first)
    regions = sorted(regions, key=lambda r: r["area"], reverse=True)
    
    # Calculate percentage change
    change_percentage = (total_changed_area / total_area) * 100 if total_area > 0 else 0.0
    
    return {
        "total_regions": len(regions),
        "total_changed_area_px": total_changed_area,
        "change_percentage": round(change_percentage, 2),
        "regions": regions
    }
