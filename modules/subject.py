import cv2
import logging
import numpy as np
from ultralytics import YOLO
from core.models import ImageRecord

logger = logging.getLogger(__name__)

# Load the nano YOLOv8 model for maximum speed and lowest VRAM usage.
# First run will download 'yolov8n.pt' automatically.
model = YOLO('yolov8n.pt')

def calculate_visibility(area_percentage: float, confidence: float) -> float:
    """
    Calculates subject_visibility_score.
    Inputs:
    - area_percentage: Float (0 to 100), the percentage of the frame the subject takes up.
    - confidence: Float (0.0 to 1.0), the model's confidence that it is a subject (person).
    
    Logic:
    - A person taking up 15% or more of the frame is considered highly visible (size_factor = 1.0).
    - If they take up less, the size_factor scales linearly.
    - Visibility = size_factor * confidence
    
    Expected Range: 0.0 to 1.0
    """
    # Cap size factor at 1.0 once the subject is reasonably large (15% of frame)
    size_factor = min(1.0, area_percentage / 15.0)
    return float(size_factor * confidence)

def process_subject(record: ImageRecord) -> ImageRecord:
    if not record.preview_path:
        return record
        
    try:
        # Run YOLO inference
        # Classes=0 restricts detection to 'person' only
        results = model(record.preview_path, classes=0, verbose=False)
        
        boxes = results[0].boxes
        
        record.subject_count = len(boxes)
        record.subject_boxes = []
        
        if len(boxes) > 0:
            # We will base the primary subject metrics on the largest/most confident person
            best_confidence = 0.0
            best_area_percentage = 0.0
            
            # Read original image dimensions for localized sharpness calculation
            # We already have preview_width and preview_height from Phase 3, but let's use cached grayscale
            gray_img = record.image_gray if hasattr(record, 'image_gray') and record.image_gray is not None else cv2.imread(record.preview_path, cv2.IMREAD_GRAYSCALE)
            total_img_area = record.preview_width * record.preview_height
            
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                
                box_w = x2 - x1
                box_h = y2 - y1
                box_area = box_w * box_h
                area_pct = (box_area / total_img_area) * 100
                
                record.subject_boxes.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "confidence": conf,
                    "area_pct": area_pct
                })
                
                # Update 'primary' subject metrics (largest area)
                if area_pct > best_area_percentage:
                    best_area_percentage = area_pct
                    best_confidence = conf
                    
                    # Calculate localized subject sharpness
                    if gray_img is not None:
                        # Extract the region of interest
                        roi = gray_img[int(y1):int(y2), int(x1):int(x2)]
                        if roi.size > 0:
                            record.subject_sharpness = float(cv2.Laplacian(roi, cv2.CV_64F).var())
            
            record.primary_subject_method = "largest_box"
            record.subject_confidence = best_confidence
            record.subject_area_percentage = best_area_percentage
            record.subject_visibility_score = calculate_visibility(best_area_percentage, best_confidence)
        else:
            # Defaults for no subjects
            record.subject_confidence = 0.0
            record.subject_area_percentage = 0.0
            record.subject_visibility_score = 0.0
            
    except Exception as e:
        logger.error(f"Module 'SubjectAnalysis' failed on '{record.filename}'. Reason: {str(e)}. Action: Skipping subject analysis.")
        
    return record

def subject_analysis_module():
    def _module(record: ImageRecord) -> ImageRecord:
        return process_subject(record)
    _module.__name__ = "SubjectAnalysis"
    return _module
