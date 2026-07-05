import cv2
import numpy as np
import logging
from core.models import ImageRecord

logger = logging.getLogger(__name__)

def process_exposure(record: ImageRecord) -> ImageRecord:
    if not record.preview_path:
        return record
        
    try:
        # Load grayscale to analyze global luminance
        img = cv2.imread(record.preview_path, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            return record
            
        # Calculate 256-bin histogram
        hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        total_pixels = img.shape[0] * img.shape[1]
        
        # Underexposure score: Percentage of pixels in the 0-15 intensity range (shadows/blacks)
        under_pixels = np.sum(hist[:15])
        record.underexposure_score = float((under_pixels / total_pixels) * 100)
        
        # Overexposure score: Percentage of pixels in the 240-255 intensity range (clipped highlights)
        over_pixels = np.sum(hist[241:])
        record.overexposure_score = float((over_pixels / total_pixels) * 100)
        
    except Exception as e:
        logger.error(f"Error in exposure analysis for {record.filename}: {e}")
        
    return record

def exposure_analysis_module():
    def _module(record: ImageRecord) -> ImageRecord:
        return process_exposure(record)
    _module.__name__ = "ExposureAnalysis"
    return _module
