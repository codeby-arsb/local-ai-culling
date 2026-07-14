import json
import os
import logging
from typing import List
from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


def export_metadata(records: List[ImageRecord], output_dir: str):
    """
    Exports all available spatial data for an image to a side-car JSON file.
    This powers the Scene Intelligence overlays in the frontend dashboard.
    """
    metadata_dir = os.path.join(output_dir, ".internal", "metadata")
    os.makedirs(metadata_dir, exist_ok=True)

    for record in records:
        if not record.filename:
            continue

        json_path = os.path.join(metadata_dir, f"{record.filename}.json")

        # Schema definition
        metadata = {
            "schema_version": 1,
            "image": {"width": record.preview_width, "height": record.preview_height},
            "faces": [],
            "subjects": [],
            "pose": {},
            "scene": {},
        }

        # 1. Subjects Layer
        if record.subject_boxes:
            for box in record.subject_boxes:
                metadata["subjects"].append(
                    {
                        "coords": [box["x1"], box["y1"], box["x2"], box["y2"]],
                        "confidence": box.get("confidence", 0.0),
                        "area_pct": box.get("area_pct", 0.0),
                    }
                )

        # 2. Faces Layer
        if record.face_boxes:
            for box in record.face_boxes:
                metadata["faces"].append(
                    {
                        "coords": [box["x1"], box["y1"], box["x2"], box["y2"]],
                        "confidence": box.get("confidence", 0.0),
                        "area_pct": box.get("area_pct", 0.0),
                        "ear": box.get("ear", 0.0),
                        "landmarks": box.get("landmarks", []),
                        "eye_state": box.get("eye_state", "Unknown"),
                        "eye_score": box.get("eye_score", 0.0),
                        "expression_type": box.get("expression_type", "Unknown"),
                        "expression_confidence": box.get("expression_confidence", 0.0),
                    }
                )

        try:
            with open(json_path, "w") as f:
                json.dump(metadata, f, separators=(",", ":"))
        except Exception as e:
            logger.error(f"Failed to write metadata for {record.filename}: {e}")
