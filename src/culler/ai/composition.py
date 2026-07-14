import cv2
import math
import numpy as np
import logging
from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


def process_composition(record: ImageRecord) -> ImageRecord:
    if not record.preview_path:
        return record

    try:
        # Load grayscale
        img = (
            record.image_gray
            if hasattr(record, "image_gray") and record.image_gray is not None
            else cv2.imread(record.preview_path, cv2.IMREAD_GRAYSCALE)
        )
        if img is None:
            logger.error(
                f"Module 'CompositionAnalysis' failed on '{record.filename}'. Reason: Image could not be loaded. Action: Skipping composition analysis."
            )
            return record

        # Detect edges
        edges = cv2.Canny(img, 50, 150, apertureSize=3)

        # Detect lines using Hough Transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is not None:
            horizontal_angles = []

            for line in lines:
                _, theta = line[0]
                angle_deg = math.degrees(theta)

                # Check if the line is roughly horizontal (near 90 degrees)
                # We consider lines between 70 and 110 degrees as candidates for horizon
                if 70 <= angle_deg <= 110:
                    # Tilt angle relative to perfect horizontal (90 degrees)
                    tilt = angle_deg - 90
                    horizontal_angles.append(tilt)

            if horizontal_angles:
                # Average tilt of the detected horizontal lines
                avg_tilt = sum(horizontal_angles) / len(horizontal_angles)
                record.tilt_angle = float(avg_tilt)

                # Basic composition score: lower tilt = better composition (simple heuristic)
                # Max penalty at 20 degrees off horizontal
                penalty = min(1.0, abs(avg_tilt) / 20.0)
                record.composition_score = float(1.0 - penalty)
            else:
                record.tilt_angle = 0.0
                record.composition_score = 1.0  # Neutral if no horizon detected
        else:
            record.tilt_angle = 0.0
            record.composition_score = 1.0

    except Exception as e:
        logger.error(
            f"Module 'CompositionAnalysis' failed on '{record.filename}'. Reason: {str(e)}. Action: Skipping composition analysis."
        )

    return record


def composition_analysis_module():
    def _module(record: ImageRecord) -> ImageRecord:
        return process_composition(record)

    _module.__name__ = "CompositionAnalysis"
    return _module
