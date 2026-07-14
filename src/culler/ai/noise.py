import cv2
import numpy as np
import logging
from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


def process_noise(record: ImageRecord) -> ImageRecord:
    if not record.preview_path:
        return record

    try:
        img = cv2.imread(record.preview_path, cv2.IMREAD_COLOR)
        if img is None:
            return record

        # --- Luminance Noise ---
        # Strategy: Subtract a median-blurred version of the image from the original.
        # This removes large structural edges and leaves high-frequency noise.
        # The standard deviation of the residual gives a fast noise estimate.
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_gray = cv2.medianBlur(gray, 5)
        noise_gray = cv2.absdiff(gray, blur_gray)

        record.luminance_noise = float(np.std(noise_gray))

        # --- Color Noise ---
        # Convert to YCrCb space to separate color channels (chrominance)
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        cr = ycrcb[:, :, 1]
        cb = ycrcb[:, :, 2]

        blur_cr = cv2.medianBlur(cr, 5)
        noise_cr = cv2.absdiff(cr, blur_cr)

        blur_cb = cv2.medianBlur(cb, 5)
        noise_cb = cv2.absdiff(cb, blur_cb)

        # Average the noise from both color channels
        record.color_noise = float((np.std(noise_cr) + np.std(noise_cb)) / 2.0)

    except Exception as e:
        logger.error(f"Error in noise analysis for {record.filename}: {e}")

    return record


def noise_analysis_module():
    def _module(record: ImageRecord) -> ImageRecord:
        return process_noise(record)

    _module.__name__ = "NoiseAnalysis"
    return _module
