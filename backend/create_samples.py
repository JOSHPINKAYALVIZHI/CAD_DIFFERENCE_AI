import cv2
import numpy as np
import os

# Create directory for samples
os.makedirs("samples", exist_ok=True)

# Image dimensions
w, h = 1000, 700

# ==========================================
# 1. Generate Image A (Reference Version 1.0)
# ==========================================
img_a = np.ones((h, w, 3), dtype=np.uint8) * 255

# Outer frame border
cv2.rectangle(img_a, (50, 50), (950, 650), (0, 0, 0), 3)

# Grid layout division lines
cv2.line(img_a, (300, 50), (300, 650), (0, 0, 0), 1)
cv2.line(img_a, (700, 50), (700, 650), (0, 0, 0), 1)
cv2.line(img_a, (50, 350), (950, 350), (0, 0, 0), 1)

# VALVE PART (Top-Left quadrant)
cv2.circle(img_a, (175, 200), 50, (0, 0, 0), 2)
cv2.circle(img_a, (175, 200), 10, (0, 0, 0), -1)  # Drill hole
cv2.putText(img_a, "VALVE ASSEMBLY", (80, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

# SUPPORT BEAM PART (Top-Center quadrant)
cv2.rectangle(img_a, (400, 150), (600, 250), (0, 0, 0), 2)
cv2.line(img_a, (400, 150), (600, 250), (0, 0, 0), 1)
cv2.line(img_a, (600, 150), (400, 250), (0, 0, 0), 1)
cv2.putText(img_a, "SUPPORT BEAM", (430, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

# BASE PLATE PART (Bottom-Left quadrant)
cv2.rectangle(img_a, (100, 450), (250, 550), (0, 0, 0), 2)
cv2.circle(img_a, (130, 500), 15, (0, 0, 0), 2)
cv2.circle(img_a, (220, 500), 15, (0, 0, 0), 2)
cv2.putText(img_a, "BASE PLATE", (115, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

# Title Block (Bottom-Right quadrant)
cv2.rectangle(img_a, (720, 500), (930, 630), (0, 0, 0), 2)
cv2.putText(img_a, "PROJECT: ENGINE BLOCK", (730, 530), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
cv2.putText(img_a, "SCALE: 1:5", (730, 560), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
cv2.putText(img_a, "DWG VER: 1.0", (730, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# Write original
cv2.imwrite("samples/drawing_v1.png", img_a)


# ==========================================
# 2. Generate Image B (Comparison Version 1.1)
# ==========================================
# Copy the original drawing
img_b = img_a.copy()

# Apply a translation (15px X, -10px Y) to simulate scan offset/misalignment
M = np.float32([[1, 0, 15], [0, 1, -10]])
img_b = cv2.warpAffine(img_b, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

# Make manual structural edits in shifted coordinates:
# A. REMOVE the drill hole in VALVE ASSEMBLY (shifted location: 175+15, 200-10 = 190, 190)
cv2.circle(img_b, (190, 190), 12, (255, 255, 255), -1)

# B. ADD a new COUPLER block (Bottom-Center quadrant)
cv2.rectangle(img_b, (420, 440), (580, 540), (0, 0, 0), 2)
cv2.circle(img_b, (500, 490), 20, (0, 0, 0), 2)
cv2.putText(img_b, "NEW COUPLER", (435, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

# C. MODIFY the Version label in the title block from 1.0 to 1.1 (shifted location: 730+15, 590-10 = 745, 580)
# Erase old text area
cv2.rectangle(img_b, (742, 568), (870, 595), (255, 255, 255), -1)
# Draw updated version
cv2.putText(img_b, "DWG VER: 1.1", (745, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# Write shifted and edited image
cv2.imwrite("samples/drawing_v2.png", img_b)

print("Generated sample files in backend/samples/:")
print("- drawing_v1.png (Reference Drawing v1.0)")
print("- drawing_v2.png (Comparison Drawing v1.1 - Translated & Modified)")
