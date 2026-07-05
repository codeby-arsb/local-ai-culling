import cv2
import logging
from core.models import ImageRecord
from datetime import datetime

logger = logging.getLogger(__name__)

def process_blur(record: ImageRecord) -> ImageRecord:
    if not record.preview_path:
        return record
        
    try:
        # Use cached grayscale image if available
        img = record.image_gray if hasattr(record, 'image_gray') and record.image_gray is not None else cv2.imread(record.preview_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            logger.error(f"Module 'BlurAnalysis' failed on '{record.filename}'. Reason: Image could not be loaded. Action: Skipping blur analysis.")
            return record
            
        # Update preview dimensions natively here
        h, w = img.shape[:2]
        record.preview_width = w
        record.preview_height = h
            
        # Calculate Laplacian variance (global sharpness estimation)
        # Higher variance = more edges = sharper. Lower variance = blurrier.
        variance = cv2.Laplacian(img, cv2.CV_64F).var()
        
        record.global_sharpness = float(variance)
        record.blur_score = float(variance) # Retained for generic sorting
        
        # Subject, Face, and Eye sharpness will be populated locally by
        # bounding-box specific masking in later phases.
        # Leaving them None for Phase 3.
        
    except Exception as e:
        logger.error(f"Module 'BlurAnalysis' failed on '{record.filename}'. Reason: {str(e)}. Action: Skipping blur analysis.")
        
    return record

def blur_analysis_module():
    def _module(record: ImageRecord) -> ImageRecord:
        return process_blur(record)
    _module.__name__ = "BlurAnalysis"
    return _module
