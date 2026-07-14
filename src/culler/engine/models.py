from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ClassificationType(str, Enum):
    KEEP = "KEEP"
    REVIEW = "REVIEW"
    REJECT = "REJECT"
    UNCLASSIFIED = "UNCLASSIFIED"


class ExifData(BaseModel):
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[float] = None
    capture_time: Optional[datetime] = None


class ImageRecord(BaseModel):
    # --- System Metadata ---
    analysis_version: str = "1.0"
    processing_timestamp: Optional[datetime] = None

    # --- File Information ---
    original_path: str
    preview_path: Optional[str] = None
    filename: str
    file_extension: str
    preview_width: Optional[int] = None
    preview_height: Optional[int] = None

    # --- EXIF Metadata ---
    exif: ExifData = Field(default_factory=ExifData)

    # --- Classification ---
    classification: ClassificationType = ClassificationType.UNCLASSIFIED
    classification_reasons: List[str] = Field(default_factory=list)

    # --- 1. Technical Metrics (Blur, Exposure, Noise) ---
    blur_score: Optional[float] = None
    global_sharpness: Optional[float] = None
    subject_sharpness: Optional[float] = None
    face_sharpness: Optional[float] = None
    eye_sharpness: Optional[float] = None

    underexposure_score: Optional[float] = None
    overexposure_score: Optional[float] = None
    luminance_noise: Optional[float] = None
    color_noise: Optional[float] = None

    # --- 1.5 Editability Engine ---
    editability_score: Optional[float] = None
    editability_confidence: Optional[float] = None
    shadow_recovery_score: Optional[float] = None
    highlight_recovery_score: Optional[float] = None
    recovery_noise: Optional[float] = None
    recovery_failure_reason: Optional[str] = None

    # --- 2. Subject Metrics ---
    subject_count: Optional[int] = None
    primary_subject_method: Optional[str] = None
    subject_confidence: Optional[float] = None
    subject_area_percentage: Optional[float] = None
    subject_visibility_score: Optional[float] = None
    subject_boxes: List[Dict[str, Any]] = Field(default_factory=list)

    # --- 3. Face Metrics ---
    face_count: Optional[int] = None
    face_confidence: Optional[float] = None
    face_boxes: List[Dict[str, Any]] = Field(default_factory=list)
    primary_face_index: Optional[int] = None
    number_of_faces: Optional[int] = None
    largest_face_ratio: Optional[float] = None

    # --- 3.5 Expression Intelligence ---
    eye_state: Optional[str] = None
    eye_state_score: Optional[float] = None
    expression_score: Optional[float] = None
    expression_confidence: Optional[float] = None
    expression_type: Optional[str] = None
    face_visibility_score: Optional[float] = None
    face_quality_score: Optional[float] = None

    # Legacy fields
    eye_confidence: Optional[float] = None

    # --- 4. Composition Metrics ---
    tilt_angle: Optional[float] = None
    composition_score: Optional[float] = None

    # --- 5. Duplicate Detection ---
    duplicate_group_id: Optional[str] = None
    perceptual_hash: Optional[str] = None
    similarity_score: Optional[float] = None

    # --- 6. Burst Ranking ---
    is_best_frame: bool = False
    burst_rank_score: Optional[float] = None
    burst_rank_position: Optional[int] = None
    ranking_reasons: List[str] = Field(default_factory=list)

    # --- 7. Classification ---
    classification: Optional[str] = None
    classification_score: Optional[float] = None
    confidence_score: Optional[float] = None
    classification_reasons: List[str] = Field(default_factory=list)

    # --- Telemetry ---
    processing_time_ms: Optional[float] = None

    # --- Transient Data (Not serialized) ---
    image_bgr: Any = Field(default=None, exclude=True)
    image_gray: Any = Field(default=None, exclude=True)

    def get_human_readable_reasons(self) -> str:
        positives = []
        warnings = []

        # Positives
        if self.is_best_frame:
            positives.append("✓ Burst Winner")
        if self.eye_state == "Open":
            positives.append("✓ Eyes Open")
        if self.editability_score is not None and self.editability_score >= -5.0:
            positives.append("✓ Excellent Editability")
        if (
            self.face_visibility_score is not None
            and self.face_visibility_score >= 90.0
        ):
            positives.append("✓ Face Fully Visible")
        if self.expression_type == "Smile":
            positives.append("✓ Smiling")

        # Warnings
        if self.blur_score is not None:
            if self.blur_score >= 50.0:
                warnings.append("⚠ Severe Blur")
            elif self.blur_score >= 20.0:
                warnings.append("⚠ Slight Motion Blur")
        if self.luminance_noise is not None:
            if self.luminance_noise >= 30.0:
                warnings.append("⚠ High Noise")
            elif self.luminance_noise >= 15.0:
                warnings.append("⚠ Moderate Noise")
        if self.underexposure_score is not None and self.underexposure_score > 20.0:
            warnings.append("⚠ Underexposed")
        if self.overexposure_score is not None and self.overexposure_score > 15.0:
            warnings.append("⚠ Overexposed")
        if self.eye_state == "Closed":
            warnings.append("⚠ Eyes Closed")
        if self.eye_state == "Mid Blink":
            warnings.append("⚠ Mid Blink")
        if self.expression_type == "Mouth Open":
            warnings.append("⚠ Mouth Open")
        if self.face_visibility_score is not None and self.face_visibility_score < 90.0:
            warnings.append("⚠ Low Face Visibility")

        return " | ".join(positives + warnings)
