import logging
import uuid
from typing import List
from abc import ABC, abstractmethod
from PIL import Image
import imagehash
from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


class DuplicateDetectionBackend(ABC):
    @abstractmethod
    def extract_features(self, image_path: str) -> str:
        """Extracts features (e.g. hash string or embedding) from an image."""
        pass

    @abstractmethod
    def calculate_distance(self, feature1: str, feature2: str) -> float:
        """Calculates the distance between two features. Lower = more similar."""
        pass


class ImageHashBackend(DuplicateDetectionBackend):
    def __init__(self, hash_size: int = 8):
        self.hash_size = hash_size

    def extract_features(self, image_path: str) -> str:
        try:
            img = Image.open(image_path)
            # Use perceptual hash (pHash) which handles minor alterations well
            phash = imagehash.phash(img, hash_size=self.hash_size)
            return str(phash)
        except Exception as e:
            logger.error(f"Error extracting pHash for {image_path}: {e}")
            return ""

    def calculate_distance(self, feature1: str, feature2: str) -> float:
        if not feature1 or not feature2:
            return float("inf")
        try:
            hash1 = imagehash.hex_to_hash(feature1)
            hash2 = imagehash.hex_to_hash(feature2)
            # Hamming distance
            return float(hash1 - hash2)
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return float("inf")


def group_duplicates(
    records: List[ImageRecord],
    backend: DuplicateDetectionBackend = None,
    threshold: float = 10.0,
    time_window_seconds: float = 10.0,
) -> List[ImageRecord]:
    """
    Groups consecutive near-duplicate images.
    Expects records to be temporally ordered (by capture time or filename).
    """
    if not backend:
        backend = ImageHashBackend()

    logger.info("Starting duplicate detection grouping...")

    # Pre-calculate hashes for all records
    for r in records:
        if r.preview_path and not r.perceptual_hash:
            r.perceptual_hash = backend.extract_features(r.preview_path)

    # Sort chronologically or alphabetically
    def get_sort_key(r: ImageRecord):
        if r.exif and r.exif.capture_time:
            return r.exif.capture_time.timestamp()
        return r.filename

    records = sorted(records, key=get_sort_key)

    current_group_id = None
    anchor_record = None

    group_count = 0
    duplicate_count = 0

    for record in records:
        if not record.perceptual_hash:
            continue

        is_duplicate = False
        if anchor_record and anchor_record.perceptual_hash:
            time_diff = 0.0
            if (
                record.exif
                and record.exif.capture_time
                and anchor_record.exif
                and anchor_record.exif.capture_time
            ):
                time_diff = abs(
                    (
                        record.exif.capture_time - anchor_record.exif.capture_time
                    ).total_seconds()
                )

            distance = backend.calculate_distance(
                record.perceptual_hash, anchor_record.perceptual_hash
            )

            # Note: We record similarity score as an inverse mapping where 1.0 is identical
            record.similarity_score = max(0.0, 1.0 - (distance / 64.0))

            # Condition for duplicate: within temporal window and visually similar to anchor
            if time_diff <= time_window_seconds and distance <= threshold:
                is_duplicate = True

        if is_duplicate:
            record.duplicate_group_id = current_group_id
            duplicate_count += 1
        else:
            # Start a new group
            current_group_id = str(uuid.uuid4())[:8]  # short human-readable group ID
            record.duplicate_group_id = current_group_id
            record.similarity_score = 1.0  # Anchor is identical to itself
            anchor_record = record  # Update anchor to the new distinct scene
            group_count += 1

    logger.info(
        f"Duplicate detection complete: Found {group_count} unique groups covering {duplicate_count} duplicates."
    )
    return records


def rank_burst_groups(records: List[ImageRecord]) -> List[ImageRecord]:
    """
    Evaluates burst groups and ranks the frames within each group
    based on Subject Sharpness, Visibility, Face Sharpness, etc.
    """
    from collections import defaultdict

    logger.info("Starting Best Frame Selection (Burst Ranking)...")

    groups = defaultdict(list)
    for r in records:
        if r.duplicate_group_id:
            groups[r.duplicate_group_id].append(r)

    for _, group_records in groups.items():
        if len(group_records) <= 1:
            if len(group_records) == 1:
                group_records[0].is_best_frame = True
                group_records[0].burst_rank_position = 1
                group_records[0].burst_rank_score = 0.0
                group_records[0].ranking_reasons = ["Singleton group"]
            continue

        for r in group_records:
            score = 0.0
            reasons = []

            # 1. Subject Sharpness (Highest Priority)
            ss = r.subject_sharpness or 0.0
            score += min(ss, 500) * 0.4
            if ss > 100:
                reasons.append("High Subject Sharpness")

            # 2. Subject Visibility
            sv = r.subject_visibility_score or 0.0
            score += sv * 100 * 0.3
            if sv > 0.7:
                reasons.append("Good Subject Visibility")

            # 3. Face Sharpness
            fs = r.face_sharpness or 0.0
            score += min(fs, 500) * 0.2
            if fs > 100:
                reasons.append("High Face Sharpness")

            # 4. Face Confidence
            fc = r.face_confidence or 0.0
            score += fc * 100 * 0.1
            if fc > 0.6:
                reasons.append("Confident Face Detection")

            # 5. Noise Penalty
            ln = r.luminance_noise or 0.0
            score -= ln * 5.0
            if ln > 4.0:
                reasons.append("High Noise Penalty")

            # 6. Exposure Penalty (Weak)
            ue = r.underexposure_score or 0.0
            score -= min(ue, 50) * 0.5
            if ue > 30:
                reasons.append("Underexposure Penalty")

            if not reasons:
                reasons.append("Baseline metrics")

            r.burst_rank_score = score
            r.ranking_reasons = reasons

        # Sort group by score descending
        group_records.sort(key=lambda x: x.burst_rank_score or 0.0, reverse=True)

        for idx, r in enumerate(group_records):
            r.burst_rank_position = idx + 1
            if idx == 0:
                r.is_best_frame = True
                r.ranking_reasons.insert(0, "Rank #1")
            elif idx == 1:
                r.ranking_reasons.insert(0, "Rank #2")
            elif idx == 2:
                r.ranking_reasons.insert(0, "Rank #3")
            else:
                r.ranking_reasons.insert(0, f"Rank #{idx + 1}")

    logger.info(f"Burst ranking complete for {len(groups)} groups.")
    return records
