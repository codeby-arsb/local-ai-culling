import os
import csv
import logging
from pathlib import Path
from typing import List

from core.models import ImageRecord
from core.config import AppConfig

logger = logging.getLogger(__name__)

def run_final_export(records: List[ImageRecord], output_dir: Path):
    """
    Executes the final export stage, creating KEEP, REVIEW, and REJECT folders
    populated with hardlinks to the original files based on ranking.
    Also generates a clean final_export.csv report and README.txt.
    """
    logger.info("Starting Phase 7: Final Export Engine...")
    
    mode = AppConfig.get("export.mode", "hardlink")
    prefix_rank = AppConfig.get("export.prefix_rank", False)
    
    # 1. Create output folders
    dirs = {
        "KEEP": output_dir / "KEEP",
        "REVIEW": output_dir / "REVIEW",
        "REJECT": output_dir / "REJECT",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
        # Clear existing
        for f in d.iterdir():
            if f.is_file():
                f.unlink()
                
    # 2. Check Volume Restrictions (if mode is hardlink and we have records)
    if mode == "hardlink" and records:
        # Check first valid record
        for r in records:
            if r.original_path:
                src_drive = os.path.splitdrive(os.path.abspath(r.original_path))[0].lower()
                dst_drive = os.path.splitdrive(os.path.abspath(output_dir))[0].lower()
                if src_drive != dst_drive:
                    error_msg = (
                        f"Export aborted: Hardlinks require input and output directories to be on the same storage volume. "
                        f"Input is on '{src_drive}', Output is on '{dst_drive}'."
                    )
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                break

    # 3. Categorize and Sort
    grouped = {"KEEP": [], "REVIEW": [], "REJECT": []}
    for r in records:
        if r.classification in grouped and r.original_path:
            grouped[r.classification].append(r)
            
    # Sort priority: 1. Classification Score, 2. Burst Winner, 3. Confidence Score, 4. Filename
    # Python sorting is stable. We sort by least important first (Filename ascending), 
    # then by the other criteria descending.
    for cls in ["KEEP", "REVIEW"]:
        grouped[cls].sort(key=lambda x: x.filename)
        grouped[cls].sort(
            key=lambda x: (
                x.classification_score or 0.0,
                1 if x.is_best_frame else 0,
                x.confidence_score or 0.0
            ),
            reverse=True
        )
    # REJECT doesn't need ranking according to requirements, but we'll sort by filename for consistency
    grouped["REJECT"].sort(key=lambda x: x.filename)
    
    # 4. Generate Hardlinks and collect CSV data
    csv_data = []
    
    for cls, cl_records in grouped.items():
        for rank_idx, r in enumerate(cl_records):
            rank = rank_idx + 1
            
            # Determine target filename
            target_filename = r.filename
            if prefix_rank and cls != "REJECT":
                target_filename = f"{rank:04d}_{r.filename}"
                
            target_path = dirs[cls] / target_filename
            
            # Create hardlink
            if mode == "hardlink":
                try:
                    os.link(r.original_path, target_path)
                except Exception as e:
                    logger.error(f"Failed to create hardlink for {r.original_path}: {e}")
            else:
                logger.warning(f"Unsupported export mode '{mode}'. Skipping {r.filename}.")
                
            # Collect CSV row
            csv_data.append({
                "Export Rank": rank if cls != "REJECT" else "",
                "Filename": r.filename,
                "Decision": cls,
                "Classification Score": round(r.classification_score, 2) if r.classification_score is not None else "",
                "Confidence": round(r.confidence_score, 2) if r.confidence_score is not None else "",
                "Editability": round(r.editability_score, 2) if r.editability_score is not None else "",
                "Expression": r.expression_type or "",
                "Eye State": r.eye_state or "",
                "Burst Rank": r.burst_rank_position if r.burst_rank_position is not None else "",
                "Best Frame": "Yes" if r.is_best_frame else "No",
                "Reasons": r.get_human_readable_reasons(),
                "Duplicate Group": r.duplicate_group_id or "",
                "Recovery Failure": r.recovery_failure_reason or "",
                "Source Path": r.original_path
            })
            
    # 5. Generate CSV
    csv_path = output_dir / "final_export.csv"
    if csv_data:
        fieldnames = list(csv_data[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        logger.info(f"Saved Final Export CSV to {csv_path}")
        
    # 6. Generate README.txt
    readme_path = output_dir / "README.txt"
    readme_content = (
        "=======================================\n"
        " Local AI Culling - Export Details\n"
        "=======================================\n\n"
        "This directory contains the final culled results of your photoshoot.\n\n"
        "• KEEP contains the strongest images ranked by quality.\n"
        "• REVIEW contains borderline images requiring manual inspection.\n"
        "• REJECT contains images the AI determined are unlikely to be delivered.\n\n"
        "• All exported files are hardlinks. They consume zero additional storage space.\n"
        "• The original photographs remain completely untouched.\n\n"
        "You can import these folders directly into Adobe Lightroom or your editor of choice.\n"
    )
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    logger.info("Final Export Engine complete.")
