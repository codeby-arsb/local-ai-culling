import cv2
import numpy as np
import logging
from typing import Callable
from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


def editability_analysis_module() -> Callable[[ImageRecord], ImageRecord]:
    def analyze_editability(record: ImageRecord) -> ImageRecord:
        if not record.preview_path:
            return record

        try:
            # Read image
            if hasattr(record, "image_bgr") and record.image_bgr is not None:
                img_bgr = record.image_bgr
            else:
                img_bgr = cv2.imread(record.preview_path)

            if img_bgr is None:
                logger.error(
                    f"Module 'EditabilityEngine' failed on '{record.filename}'. Reason: Image could not be loaded. Action: Skipping editability analysis."
                )
                return record

            # Downscale for performance if very large, but preview is usually small enough
            # We want this to be extremely fast.
            h, w = img_bgr.shape[:2]
            if w > 640:
                scale = 640 / w
                img_bgr = cv2.resize(img_bgr, (640, int(h * scale)))

            img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            v_channel = img_hsv[:, :, 2]

            # 1. Shadow Recovery Simulation
            # Target deeply underexposed areas
            shadow_mask = cv2.inRange(v_channel, 0, 60)
            shadow_ratio = cv2.countNonZero(shadow_mask) / (img_gray.size)

            shadow_penalty = 0.0
            recovery_noise = 0.0

            if (
                shadow_ratio > 0.02
            ):  # Only penalize if more than 2% of image is deep shadows
                # Simulate +2 EV exposure lift using gamma correction
                # gamma = 0.45 is roughly a strong shadow lift
                invGamma = 1.0 / 2.2
                table = np.array(
                    [((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]
                ).astype("uint8")
                lifted_bgr = cv2.LUT(img_bgr, table)
                lifted_gray = cv2.cvtColor(lifted_bgr, cv2.COLOR_BGR2GRAY)

                # Calculate noise in lifted shadows using Laplacian variance
                laplacian = cv2.Laplacian(lifted_gray, cv2.CV_64F)
                # We only care about the variance inside the shadow mask
                mean, stddev = cv2.meanStdDev(laplacian, mask=shadow_mask)
                variance = stddev[0][0] ** 2

                # High variance in a flat lifted shadow region implies high noise/grain
                # Normal clean shadows might have variance < 50
                # Noisy shadows might have variance > 200
                recovery_noise = min(variance / 5.0, 100.0)  # map to 0-100

                # Calculate chroma variance (color degradation)
                lifted_ycrcb = cv2.cvtColor(lifted_bgr, cv2.COLOR_BGR2YCrCb)
                _, cr_stddev = cv2.meanStdDev(lifted_ycrcb[:, :, 1], mask=shadow_mask)
                _, cb_stddev = cv2.meanStdDev(lifted_ycrcb[:, :, 2], mask=shadow_mask)
                chroma_variance = cr_stddev[0][0] ** 2 + cb_stddev[0][0] ** 2
                color_degradation = min(chroma_variance / 3.0, 100.0)

                # Combine for shadow penalty
                shadow_penalty = (recovery_noise * 0.6) + (color_degradation * 0.4)
                # Scale by how much shadow there actually is, to avoid penalizing tiny spots too heavily
                shadow_penalty = shadow_penalty * min(shadow_ratio * 5.0, 1.0)

            record.shadow_recovery_score = max(100.0 - shadow_penalty, 0.0)
            record.recovery_noise = recovery_noise

            # 2. Highlight Recovery Simulation
            # Target blown highlights
            highlight_mask = cv2.inRange(v_channel, 245, 255)
            highlight_ratio = cv2.countNonZero(highlight_mask) / (img_gray.size)

            highlight_penalty = 0.0

            if highlight_ratio > 0.01:  # More than 1% blown
                # Find pure white (R>250, G>250, B>250)
                # These are completely unrecoverable
                pure_white_mask = cv2.inRange(img_bgr, (250, 250, 250), (255, 255, 255))
                pure_white_ratio = cv2.countNonZero(pure_white_mask) / (img_gray.size)

                # If a large portion of the highlight is pure white, it's bad.
                # E.g., 5% pure white is a huge blown sky or flash reflection.
                highlight_penalty = min(pure_white_ratio * 1000.0, 100.0)

            record.highlight_recovery_score = max(100.0 - highlight_penalty, 0.0)

            # 3. Aggregation and Editability Score
            total_penalty = min(shadow_penalty + highlight_penalty, 100.0)
            record.editability_score = 100.0 - total_penalty

            # 4. Editability Confidence
            # Very dark images or very noisy images reduce confidence because the preview hides data
            mean_lum = cv2.mean(img_gray)[0]
            if mean_lum < 40:
                # Difficult lighting (concerts, dark halls) -> lower confidence
                confidence = 50.0 + mean_lum
            elif mean_lum > 220:
                # Overexposed -> lower confidence
                confidence = 100.0 - (mean_lum - 220) * 2
            else:
                # Good exposure -> high confidence
                confidence = 90.0 + (10.0 - abs(130 - mean_lum) / 10.0)

            record.editability_confidence = max(min(confidence, 100.0), 10.0)

            # 5. Recovery Failure Reason
            if total_penalty > 15.0:
                if highlight_penalty > shadow_penalty:
                    record.recovery_failure_reason = "Highlight Clipping"
                elif recovery_noise > 40.0 and color_degradation > 40.0:
                    record.recovery_failure_reason = "Shadow Noise & Color Degradation"
                elif recovery_noise > 40.0:
                    record.recovery_failure_reason = "Shadow Noise"
                elif shadow_penalty > highlight_penalty:
                    record.recovery_failure_reason = "Shadow Recovery Issues"
                else:
                    record.recovery_failure_reason = "Mixed Recovery Issues"

            logger.debug(
                f"Editability {record.filename}: Score={record.editability_score:.1f}, "
                f"Conf={record.editability_confidence:.1f}, Reason={record.recovery_failure_reason}"
            )

        except Exception as e:
            logger.error(
                f"Module 'EditabilityEngine' failed on '{record.filename}'. Reason: {str(e)}. Action: Skipping editability analysis."
            )

        return record

    return analyze_editability
