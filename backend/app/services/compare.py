import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

def locate_text_regions(gray_img: np.ndarray) -> np.ndarray:
    """
    Locates text, dimensions, labels, and text block zones on the drawing sheet
    using morphological gradient density and aspect ratio constraints.
    Returns a binary mask where 255 indicates text zones to ignore.
    """
    h, w = gray_img.shape[:2]
    text_mask = np.zeros((h, w), dtype=np.uint8)
    
    # Calculate morphological gradient to extract character strokes
    grad = cv2.morphologyEx(gray_img, cv2.MORPH_GRADIENT, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    
    # Threshold gradient
    _, thresh = cv2.threshold(grad, 50, 255, cv2.THRESH_BINARY)
    
    # Close horizontally to connect characters in words/labels
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 6))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)
    
    # Detect contour regions of candidate text zones
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        cx, cy, cw, ch = cv2.boundingRect(cnt)
        
        # Filter for typical text height on drawing sheets (7px to 35px)
        if 7 <= ch <= 35 and cw >= 5:
            # Verify average ink density in the region to avoid masking solid lines/blocks
            box_gray = gray_img[cy:cy+ch, cx:cx+cw]
            ink_density = np.mean(box_gray < 220)
            
            # Text block density typically ranges from 5% to 65% ink
            if 0.05 <= ink_density <= 0.65:
                # Add padding to cover full text height/spacing
                pad_x = 4
                pad_y = 2
                x1 = max(0, cx - pad_x)
                y1 = max(0, cy - pad_y)
                x2 = min(w, cx + cw + pad_x)
                y2 = min(h, cy + ch + pad_y)
                cv2.rectangle(text_mask, (x1, y1), (x2, y2), 255, -1)
                
    return text_mask

def detect_differences(
    ref_img: np.ndarray, 
    aligned_img: np.ndarray
) -> tuple[np.ndarray, float]:
    """
    Compares reference and aligned drawings, returning a binary difference mask and SSIM score.
    Filters out drawing borders/templates and annotation text to isolate structural design changes.
    """
    # Convert both drawings to grayscale
    gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    gray_cmp = cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY)
    
    # Calculate Structural Similarity Index (SSIM) for similarity metrics
    score, _ = ssim(gray_ref, gray_cmp, full=True)
    
    # Extract ink masks (dark pixels, typically gray < 220 on white paper to capture lighter details)
    _, ink_ref = cv2.threshold(gray_ref, 220, 255, cv2.THRESH_BINARY_INV)
    _, ink_cmp = cv2.threshold(gray_cmp, 220, 255, cv2.THRESH_BINARY_INV)
    
    # Dilate ink masks by a small kernel (3x3 provides a tight 1-pixel tolerance radius)
    # This ignores microscopic scan rendering jitter, but captures all actual design modifications.
    kernel_tolerance = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated_ref = cv2.dilate(ink_ref, kernel_tolerance)
    dilated_cmp = cv2.dilate(ink_cmp, kernel_tolerance)
    
    # True Removal: Ink was in Ref, but there is no ink anywhere in the Comp neighborhood
    true_removals = cv2.bitwise_and(ink_ref, cv2.bitwise_not(dilated_cmp))
    
    # True Addition: Ink is in Comp, but there was no ink anywhere in the Ref neighborhood
    true_additions = cv2.bitwise_and(ink_cmp, cv2.bitwise_not(dilated_ref))
    
    # Combine true removals and true additions
    combined_mask = cv2.bitwise_or(true_removals, true_additions)
    
    # Morphological closing to group adjacent segments (e.g. dots on letter i or dashed lines)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel_close)
    
    # Morphological opening to filter out single-pixel isolated noise specs
    kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned_mask = cv2.morphologyEx(closed_mask, cv2.MORPH_OPEN, kernel_open)
    
    # Locate text, labels, and dimensions on both sheets
    text_mask_ref = locate_text_regions(gray_ref)
    text_mask_cmp = locate_text_regions(gray_cmp)
    combined_text_mask = cv2.bitwise_or(text_mask_ref, text_mask_cmp)
    
    # Exclude text changes from the differences
    cleaned_mask = cv2.bitwise_and(cleaned_mask, cv2.bitwise_not(combined_text_mask))
    
    # Exclude outer border lines of the drawing template (ignore outer 4% margin boundaries)
    h, w = cleaned_mask.shape[:2]
    margin_h = int(h * 0.04)
    margin_w = int(w * 0.04)
    
    cleaned_mask[0:margin_h, :] = 0
    cleaned_mask[h-margin_h:h, :] = 0
    cleaned_mask[:, 0:margin_w] = 0
    cleaned_mask[:, w-margin_w:w] = 0
    
    return cleaned_mask, float(score)

def estimate_optimal_noise_limit(mask: np.ndarray) -> int:
    """
    Analyzes the difference mask, its resolution, and the size distribution of raw contours
    to automatically estimate the optimal noise limit.
    """
    # Find all contours in the raw difference mask (without min_area filter)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 40
        
    areas = [float(cv2.contourArea(c)) for c in contours if cv2.contourArea(c) > 5]
    if not areas:
        return 40
        
    # Default sensitive limit for clean drawings (vector PDFs or clean exports)
    base_limit = 40
    
    # Analyze distribution of contour areas to detect high-frequency noise/jitter
    tiny_contours = [a for a in areas if a < 150]
    
    # If we have a high density of contours and more than 60% are tiny, it is a noisy scan.
    # We dynamically calculate the noise floor using a 3.0x multiplier.
    if len(areas) > 15 and (len(tiny_contours) / len(areas)) > 0.60:
        median_tiny = np.median(tiny_contours) if tiny_contours else 30
        auto_limit = int(median_tiny * 3.0)
        return max(base_limit, min(auto_limit, 140))
        
    return base_limit




