import os
import shutil
import logging
from pathlib import Path
from typing import List
from PIL import Image, ImageDraw, ImageFont

from culler.engine.models import ImageRecord

logger = logging.getLogger(__name__)


def link_or_copy(src: str, dst: str):
    """Attempts to hardlink to save space, falls back to copy."""
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def generate_visual_exports(
    records: List[ImageRecord], output_dir: Path, max_samples: int = None
):
    """
    Generates preview directories and visual contact sheets to allow
    rapid human validation of classification decisions.
    """
    logger.info("Starting Phase 5C: Visual Export Generation...")

    dirs = {
        "KEEP": output_dir / "keep_preview",
        "REVIEW": output_dir / "review_preview",
        "REJECT": output_dir / "reject_preview",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
        # Clean existing files for fresh run
        for f in d.iterdir():
            if f.is_file():
                f.unlink()

    sheets_dir = output_dir / "contact_sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)

    # Categorize and sort
    grouped = {"KEEP": [], "REVIEW": [], "REJECT": []}
    for r in records:
        if r.classification in grouped and r.preview_path:
            grouped[r.classification].append(r)

    grouped["KEEP"].sort(key=lambda x: x.classification_score or 0.0, reverse=True)
    grouped["REVIEW"].sort(key=lambda x: x.classification_score or 0.0, reverse=True)
    grouped["REJECT"].sort(
        key=lambda x: x.classification_score or 0.0, reverse=False
    )  # Lowest first

    # Export previews via hardlink
    for cls, cl_records in grouped.items():
        limit = max_samples if max_samples else len(cl_records)
        for r in cl_records[:limit]:
            if r.preview_path and Path(r.preview_path).exists():
                target = dirs[cls] / r.filename
                link_or_copy(r.preview_path, str(target))

    # Contact Sheets
    def build_sheet(records_list, title, filename, color):
        if not records_list:
            return

        thumb_w, thumb_h = 300, 200
        footer_h = 60
        header_h = 100
        cols = 5
        rows = (len(records_list) + cols - 1) // cols

        sheet_w = cols * thumb_w
        sheet_h = header_h + (rows * (thumb_h + footer_h))

        sheet_img = Image.new("RGB", (sheet_w, sheet_h), color=(20, 20, 20))
        draw = ImageDraw.Draw(sheet_img)

        try:
            font = ImageFont.truetype("arial.ttf", 16)
            title_font = ImageFont.truetype("arial.ttf", 32)
        except Exception:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()

        avg_score = sum(r.classification_score or 0.0 for r in records_list) / len(
            records_list
        )
        header_text = f"{title} | Total Images: {len(records_list)} | Average Score: {avg_score:.1f}"
        draw.text((20, 30), header_text, fill=color, font=title_font)

        for idx, r in enumerate(records_list):
            if not r.preview_path or not Path(r.preview_path).exists():
                continue

            c = idx % cols
            ro = idx // cols

            x = c * thumb_w
            y = header_h + ro * (thumb_h + footer_h)

            try:
                img = Image.open(r.preview_path)
                img.thumbnail((thumb_w, thumb_h))
                # Paste centered in thumbnail area
                paste_x = x + (thumb_w - img.width) // 2
                paste_y = y + (thumb_h - img.height) // 2
                sheet_img.paste(img, (paste_x, paste_y))
            except Exception as e:
                logger.error(f"Failed to process {r.preview_path}: {e}")

            # Draw footer accent line
            draw.rectangle([x, y + thumb_h, x + thumb_w, y + thumb_h + 4], fill=color)

            # Draw text
            text_y = y + thumb_h + 10
            draw.text(
                (x + 10, text_y), f"{r.filename}", fill=(255, 255, 255), font=font
            )
            draw.text(
                (x + 10, text_y + 20),
                f"{r.classification} | Score: {r.classification_score:.1f}",
                fill=(200, 200, 200),
                font=font,
            )

        sheet_img.save(sheets_dir / filename, quality=85)

    build_sheet(grouped["KEEP"], "KEEP Classification", "keep_sheet.jpg", (50, 205, 50))
    build_sheet(
        grouped["REVIEW"], "REVIEW Classification", "review_sheet.jpg", (255, 215, 0)
    )
    build_sheet(
        grouped["REJECT"], "REJECT Classification", "reject_sheet.jpg", (220, 20, 60)
    )

    # Top KEEP
    if len(grouped["KEEP"]) > 0:
        build_sheet(
            grouped["KEEP"][:20],
            "Top KEEP Showcase",
            "top_keep_sheet.jpg",
            (50, 205, 50),
        )

    logger.info("Visual export complete.")
