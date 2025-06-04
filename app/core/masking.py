import cv2
import numpy as np
import os
import tempfile
from pathlib import Path
from ..core.config import settings

def mask_child_face(input_path):
    base_dir = Path(settings.BASE_DIR)
    prototxt = "./additional/deploy.prototxt"
    caffemodel = "./additional/res10_300x300_ssd_iter_140000.caffemodel"
    
    net = cv2.dnn.readNetFromCaffe(str(prototxt), str(caffemodel))
    
    image = cv2.imread(input_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at {input_path}")
    
    (h, w) = image.shape[:2]
    
    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (300, 300)), 
        1.0, 
        (300, 300),
        (104.0, 177.0, 123.0)
    )
    net.setInput(blob)
    detections = net.forward()
    
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.7:  
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            startX, startY = max(0, startX), max(0, startY)
            endX, endY = min(w, endX), min(h, endY)
            
            face_roi = image[startY:endY, startX:endX]
            
            blurred_face = cv2.GaussianBlur(face_roi, (99, 99), 30)
            
            image[startY:endY, startX:endX] = blurred_face
    
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(temp_file.name, image)
    
    output_dir = Path(base_dir) / "storage" / "uploads"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "mask.png"
    
    # Save the masked image using direct file writing
    with open(output_path, "wb") as buffer:
        # Encode the image to png format
        _, img_encoded = cv2.imencode('.png', image)
        buffer.write(img_encoded.tobytes())
    
    return temp_file.name