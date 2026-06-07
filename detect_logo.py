import cv2
import numpy as np

video_path = "generated/videos/ice cream.mp4"
logo_path = "assets/logo.png"

# Read logo
logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
if logo is None:
    print("Could not read logo.png")
    exit(1)

# The logo might have an alpha channel, we'll extract just the BGR part for template matching
if logo.shape[2] == 4:
    alpha = logo[:, :, 3]
    logo_bgr = logo[:, :, :3]
    # Create mask where alpha is > 0
    mask = (alpha > 0).astype(np.uint8)
else:
    logo_bgr = logo
    mask = None

# Read video frame
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
if not ret:
    print("Could not read video")
    exit(1)

height, width = frame.shape[:2]
print(f"Video Dimensions: {width}x{height}")

# Let's search across multiple possible logo scales that the user might have used
best_val = -1
best_loc = None
best_scale_size = None

for test_size in range(32, 200, 4):
    resized_logo = cv2.resize(logo_bgr, (test_size, test_size))
    if mask is not None:
        resized_mask = cv2.resize(mask, (test_size, test_size))
    else:
        resized_mask = None
        
    result = cv2.matchTemplate(frame, resized_logo, cv2.TM_CCORR_NORMED, mask=resized_mask)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val > best_val:
        best_val = max_val
        best_loc = max_loc
        best_scale_size = test_size

print(f"Best match found with size {best_scale_size}x{best_scale_size}")
print(f"Match confidence: {best_val}")

if best_val > 0.8:
    x, y = best_loc
    # Calculate margins from bottom right
    margin_right = width - (x + best_scale_size)
    margin_bottom = height - (y + best_scale_size)
    print(f"Calculated Coordinates -> X: {x}, Y: {y}")
    print(f"Calculated Margins -> margin_right: {margin_right}, margin_bottom: {margin_bottom}")
else:
    print("No strong match found. Confidence is too low.")
