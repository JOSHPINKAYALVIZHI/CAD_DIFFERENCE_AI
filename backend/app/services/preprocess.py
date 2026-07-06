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
    pix = page.get_pixmap(dpi=150)  # 150 DPI is standard for engineering drawings
    
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
