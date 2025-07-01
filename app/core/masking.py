import cv2
import numpy as np
import os
import tempfile
import logging
from pathlib import Path
from ..core.config import settings
from ..core.logger import get_logger

logger = get_logger()

def mask_child_face(input_path):
    try:
        base_dir = Path(settings.BASE_DIR)
        prototxt = "./additional/deploy.prototxt"
        caffemodel = "./additional/res10_300x300_ssd_iter_140000.caffemodel"
        
        # Load the face detection model
        try:
            net = cv2.dnn.readNetFromCaffe(str(prototxt), str(caffemodel))
        except Exception as e:
            logger.error(f"Failed to load face detection model: {str(e)}")
            raise RuntimeError(f"Failed to initialize face detection model: {str(e)}")
        
        # Read and validate input image
        try:
            image = cv2.imread(input_path)
            if image is None:
                logger.error(f"Failed to load image at path: {input_path}")
                raise FileNotFoundError(f"Image not found or invalid at {input_path}")
        except Exception as e:
            logger.error(f"Error reading image {input_path}: {str(e)}")
            raise
        
        (h, w) = image.shape[:2]
        logger.debug(f"Processing image with dimensions: {w}x{h}")
        
        try:
            blob = cv2.dnn.blobFromImage(
                cv2.resize(image, (300, 300)), 
                1.0, 
                (300, 300),
                (104.0, 177.0, 123.0)
            )
            net.setInput(blob)
            detections = net.forward()
            
            # Convert to BGRA to support transparency
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            
            faces_detected = 0
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.7:
                    faces_detected += 1
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    startX, startY = max(0, startX), max(0, startY)
                    endX, endY = min(w, endX), min(h, endY)
                    
                    # Set face region to fully transparent
                    image[startY:endY, startX:endX, 3] = 0
            
            logger.info(f"Detected and set {faces_detected} faces to transparent")
            
        except Exception as e:
            logger.error(f"Error during face detection and masking: {str(e)}")
            raise RuntimeError(f"Face detection and masking failed: {str(e)}")
        
        # Save the processed image
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            cv2.imwrite(temp_file.name, image)
            
            output_dir = Path(base_dir) / "storage" / "uploads"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / "mask.png"
            
            # Save the masked image using direct file writing
            with open(output_path, "wb") as buffer:
                _, img_encoded = cv2.imencode('.png', image)
                buffer.write(img_encoded.tobytes())
            
            logger.info(f"Successfully saved transparent-masked image to {output_path}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error saving processed image: {str(e)}")
            # Clean up temp file if it was created
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass
            raise RuntimeError(f"Failed to save processed image: {str(e)}")
            
    except Exception as e:
        logger.error(f"Unexpected error in mask_child_face: {str(e)}")
        raise