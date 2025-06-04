import cv2
import dlib
import numpy as np
from PIL import Image

def get_face_landmarks(img, detector, predictor):
    """Detect facial landmarks using dlib"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    if len(faces) == 0:
        return None
    
    face = faces[0]  # Use the first face found
    landmarks = predictor(gray, face)
    return np.array([[p.x, p.y] for p in landmarks.parts()], dtype=np.int32)

def create_face_mask(landmarks, img_shape):
    """Create a convex hull mask for the face"""
    hull = cv2.convexHull(landmarks)
    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, hull, 255)
    return mask

def align_face(source_img, source_landmarks, target_landmarks):
    """Align source face to target face using similarity transform"""
    # Select key facial points (eyes, nose, mouth corners)
    indices = [36, 45, 30, 48, 54]  # Right eye, left eye, nose, mouth corners
    
    src_pts = source_landmarks[indices].astype(np.float32)
    dst_pts = target_landmarks[indices].astype(np.float32)
    
    # Calculate transformation matrix
    M, _ = cv2.estimateAffinePartial2D(src_pts, dst_pts)
    
    # Warp the source face
    aligned_face = cv2.warpAffine(
        source_img, M, 
        (target_img.shape[1], target_img.shape[0]),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE
    )
    return aligned_face, M

def blend_faces(aligned_face, target_img, mask):
    """Seamlessly blend faces using Poisson blending"""
    # Find center of face for blending
    center = np.mean(target_landmarks, axis=0).astype(int)
    
    # Convert to BGRA for transparency handling
    aligned_face_bgra = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2BGRA)
    aligned_face_bgra[:, :, 3] = mask  # Set alpha channel
    
    # Convert target to BGRA
    target_bgra = cv2.cvtColor(target_img, cv2.COLOR_BGR2BGRA)
    
    # Create output image
    output = target_bgra.copy()
    
    # Blend using mask
    for c in range(0, 3):
        output[:, :, c] = np.where(
            mask == 255,
            aligned_face_bgra[:, :, c],
            target_bgra[:, :, c]
        )
    
    return cv2.cvtColor(output, cv2.COLOR_BGRA2BGR)

# Initialize dlib's face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

# ====== Input Images ======
# Replace with your image paths
source_path = "0de0d3bd-1b18-4fb4-900c-8243a00da7c9.jpeg"  # Image with face to swap
target_path = "0f6f2c66-e2c1-4691-a6d3-00eecf938508.png"    # Book/target image
output_path = "result.jpg"

# Load images
source_img = cv2.imread(source_path)
target_img = cv2.imread(target_path)

# Get facial landmarks
source_landmarks = get_face_landmarks(source_img, detector, predictor)
target_landmarks = get_face_landmarks(target_img, detector, predictor)

if source_landmarks is None or target_landmarks is None:
    print("Face detection failed in one or both images")
    exit()

# Create face mask for target
mask = create_face_mask(target_landmarks, target_img.shape)

# Align source face to target face
aligned_face, _ = align_face(source_img, source_landmarks, target_landmarks)

# Blend faces
result = blend_faces(aligned_face, target_img, mask)

# Save result
cv2.imwrite(output_path, result)
print(f"Face swap complete! Result saved to {output_path}")

# Optional: Display results
cv2.imshow("Source", source_img)
cv2.imshow("Target", target_path)
cv2.imshow("Result", result)
cv2.waitKey(0)
cv2.destroyAllWindows()