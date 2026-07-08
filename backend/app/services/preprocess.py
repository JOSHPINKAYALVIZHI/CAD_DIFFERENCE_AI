import fitz  # PyMuPDF
import cv2
import numpy as np
import os
from app.core.config import settings

def convert_pdf_to_image(pdf_path: str, page_num: int = 0) -> str:
    """
    Converts a PDF page to a PNG image and returns the file path.
    """
    doc = fitz.open(pdf_path)
    if page_num >= len(doc):
        page_num = 0
    page = doc.load_page(page_num)
    pix = page.get_pixmap(dpi=300)  # 300 DPI preserves original CAD resolution and prevents aliasing/margin shifts
    
    # Save to a temporary image in upload dir
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(settings.UPLOAD_DIR, f"{base_name}_page_{page_num}.png")
    pix.save(out_path)
    doc.close()
    return out_path

def align_images(ref_img: np.ndarray, cmp_img: np.ndarray) -> tuple[np.ndarray, bool]:
    """
    Aligns cmp_img to ref_img using ORB feature detection and Homography.
    Returns the aligned image and a boolean flag indicating if alignment succeeded.
    """
    # Convert to grayscale for feature matching
    gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
    gray_cmp = cv2.cvtColor(cmp_img, cv2.COLOR_BGR2GRAY)
    
    # Initialize ORB detector with higher density keypoints
    orb = cv2.ORB_create(nfeatures=8000)
    kp_ref, des_ref = orb.detectAndCompute(gray_ref, None)
    kp_cmp, des_cmp = orb.detectAndCompute(gray_cmp, None)
    
    # Fallback to standard resize if descriptor extraction fails
    if des_ref is None or des_cmp is None:
        h, w = ref_img.shape[:2]
        return cv2.resize(cmp_img, (w, h)), False
        
    # Use Brute-Force Matcher with KNN (k=2) to enable Lowe's ratio test
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(des_cmp, des_ref, k=2)
    
    # Apply Lowe's ratio test to filter out ambiguous and outlier feature matches
    good_matches = []
    for m_n in matches:
        if len(m_n) == 2:
            m, n = m_n
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
    
    # Sort matches by distance (best matches first)
    good_matches = sorted(good_matches, key=lambda x: x.distance)
    
    # We need at least 4 matches to compute homography
    if len(good_matches) < 4:
        h, w = ref_img.shape[:2]
        return cv2.resize(cmp_img, (w, h)), False
        
    # Extract locations of matched keypoints
    pts_cmp = np.float32([kp_cmp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    pts_ref = np.float32([kp_ref[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    # Find Homography matrix with a stricter RANSAC threshold (3.0px error margin)
    H, mask = cv2.findHomography(pts_cmp, pts_ref, cv2.RANSAC, 3.0)
    
    if H is None:
        h, w = ref_img.shape[:2]
        return cv2.resize(cmp_img, (w, h)), False
        
    # Warp comparison image to align with reference image, fill with white border
    h, w = ref_img.shape[:2]
    aligned_img = cv2.warpPerspective(cmp_img, H, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    
    return aligned_img, True

def crop_and_normalize_pair(img_a: np.ndarray, img_b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Crops empty white margins from both images using a joint bounding box
    and normalizes both to have scale-consistent resolutions (max dimension 1800px).
    """
    # 1. Find white border bounding box for Image A
    gray_a = cv2.cvtColor(img_a, cv2.COLOR_BGR2GRAY)
    _, thresh_a = cv2.threshold(gray_a, 240, 255, cv2.THRESH_BINARY_INV)
    coords_a = cv2.findNonZero(thresh_a)
    
    # 2. Find white border bounding box for Image B
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2GRAY)
    _, thresh_b = cv2.threshold(gray_b, 240, 255, cv2.THRESH_BINARY_INV)
    coords_b = cv2.findNonZero(thresh_b)
    
    h_a, w_a = img_a.shape[:2]
    h_b, w_b = img_b.shape[:2]
    
    # Defaults (full dimensions)
    x_min, y_min = w_a, h_a
    x_max, y_max = 0, 0
    scale_x, scale_y = 1.0, 1.0
    
    # If both images have content, find the union bounding box
    if coords_a is not None or coords_b is not None:
        if coords_a is not None:
            x, y, w, h = cv2.boundingRect(coords_a)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + w)
            y_max = max(y_max, y + h)
            
        if coords_b is not None:
            x, y, w, h = cv2.boundingRect(coords_b)
            # If B's resolution differs from A, scale B's bounding box coordinates to A's scale
            scale_x = w_a / float(w_b)
            scale_y = h_a / float(h_b)
            x_min = min(x_min, int(x * scale_x))
            y_min = min(y_min, int(y * scale_y))
            x_max = max(x_max, int((x + w) * scale_x))
            y_max = max(y_max, int((y + h) * scale_y))
            
        # Add padding (e.g. 20px)
        padding = 20
        x_start = max(0, x_min - padding)
        y_start = max(0, y_min - padding)
        x_end = min(w_a, x_max + padding)
        y_end = min(h_a, y_max + padding)
        
        # Crop Image A using A's coordinates
        img_a_cropped = img_a[y_start:y_end, x_start:x_end]
        
        # Crop Image B using B's coordinates back-projected
        x_start_b = max(0, int(x_start / scale_x))
        y_start_b = max(0, int(y_start / scale_y))
        x_end_b = min(w_b, int(x_end / scale_x))
        y_end_b = min(h_b, int(y_end / scale_y))
        img_b_cropped = img_b[y_start_b:y_end_b, x_start_b:x_end_b]
    else:
        img_a_cropped = img_a
        img_b_cropped = img_b
        
    # 3. Normalize resolution to a standard max dimension (1800px)
    max_dim = 1800
    
    # Scale A
    h_ac, w_ac = img_a_cropped.shape[:2]
    if max(h_ac, w_ac) > max_dim:
        scale = max_dim / float(max(h_ac, w_ac))
        new_w = int(w_ac * scale)
        new_h = int(h_ac * scale)
        img_a_cropped = cv2.resize(img_a_cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
    # Scale B
    h_bc, w_bc = img_b_cropped.shape[:2]
    if max(h_bc, w_bc) > max_dim:
        scale = max_dim / float(max(h_bc, w_bc))
        new_w = int(w_bc * scale)
        new_h = int(h_bc * scale)
        img_b_cropped = cv2.resize(img_b_cropped, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
    return img_a_cropped, img_b_cropped

def preprocess_and_load(file_path: str) -> np.ndarray:
    """
    Loads an image, converting from PDF if necessary.
    """
    if file_path.lower().endswith('.pdf'):
        file_path = convert_pdf_to_image(file_path)
    
    img = cv2.imread(file_path)
    if img is None:
        raise ValueError(f"Could not load image from path: {file_path}")
        
    return img
