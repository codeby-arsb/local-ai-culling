import os
from pathlib import Path
import logging
from typing import List
from datetime import datetime
import exifread

from core.models import ImageRecord, ExifData

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.arw', '.cr2', '.cr3', '.nef', '.dng'}

def parse_exif(file_path: Path) -> ExifData:
    exif_data = ExifData()
    try:
        with open(file_path, 'rb') as f:
            # We process without details to speed it up and just get the top-level info
            tags = exifread.process_file(f, details=False)
            
            if 'Image Model' in tags:
                exif_data.camera_model = str(tags['Image Model'])
            if 'EXIF LensModel' in tags:
                exif_data.lens_model = str(tags['EXIF LensModel'])
            if 'EXIF ISOSpeedRatings' in tags:
                try:
                    exif_data.iso = int(str(tags['EXIF ISOSpeedRatings']))
                except ValueError:
                    pass
            if 'EXIF FNumber' in tags:
                val = tags['EXIF FNumber'].values[0]
                if val.den != 0:
                    exif_data.aperture = float(val.num) / float(val.den)
            if 'EXIF ExposureTime' in tags:
                exif_data.shutter_speed = str(tags['EXIF ExposureTime'])
            if 'EXIF FocalLength' in tags:
                val = tags['EXIF FocalLength'].values[0]
                if val.den != 0:
                    exif_data.focal_length = float(val.num) / float(val.den)
            if 'EXIF DateTimeOriginal' in tags:
                dt_str = str(tags['EXIF DateTimeOriginal'])
                try:
                    # EXIF format is typically "YYYY:MM:DD HH:MM:SS"
                    exif_data.capture_time = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    pass
    except Exception as e:
        logger.warning(f"Failed to read EXIF for {file_path.name}: {e}")
        
    return exif_data

def ingest_folder(input_folder: Path) -> List[ImageRecord]:
    """Scans the input folder, reads basic EXIF, and initializes ImageRecords."""
    records = []
    
    if not input_folder.exists() or not input_folder.is_dir():
        logger.error(f"Input folder not found: {input_folder}")
        return records

    logger.info(f"Scanning {input_folder} for supported images...")
    
    for root, _, files in os.walk(input_folder):
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            if ext in SUPPORTED_EXTENSIONS:
                # Read EXIF directly from the file to avoid decoding the image payload
                exif = parse_exif(file_path)
                
                # Create ImageRecord
                record = ImageRecord(
                    original_path=str(file_path),
                    filename=file_path.name,
                    file_extension=ext,
                    exif=exif
                )
                records.append(record)
                
    logger.info(f"Ingested {len(records)} images.")
    return records
