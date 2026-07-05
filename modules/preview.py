import logging
from pathlib import Path
from PIL import Image
import rawpy

from core.models import ImageRecord

logger = logging.getLogger(__name__)

# Max dimensions for preview images to save RAM in subsequent processing
PREVIEW_MAX_SIZE = (1920, 1080)

def generate_preview(record: ImageRecord, cache_dir: Path) -> ImageRecord:
    """
    Extracts embedded preview from RAW, or resizes JPEG/PNG, 
    and saves it to the cache directory. Updates record.preview_path.
    """
    original_path = Path(record.original_path)
    
    # Create a unique preview name
    preview_filename = f"{original_path.stem}_{hash(str(original_path))}.jpg"
    preview_path = cache_dir / preview_filename
    
    if preview_path.exists():
        record.preview_path = str(preview_path)
        return record
        
    ext = record.file_extension.lower()
    
    try:
        if ext in {'.arw', '.cr2', '.cr3', '.nef', '.dng'}:
            # Attempt to extract embedded JPEG using rawpy
            try:
                with rawpy.imread(str(original_path)) as raw:
                    try:
                        thumb = raw.extract_thumb()
                        if thumb.format == rawpy.ThumbFormat.JPEG:
                            with open(preview_path, 'wb') as f:
                                f.write(thumb.data)
                        elif thumb.format == rawpy.ThumbFormat.BITMAP:
                            # Not a JPEG preview, fallback to pillow
                            image = Image.fromarray(thumb.data)
                            image.thumbnail(PREVIEW_MAX_SIZE)
                            image.save(preview_path, "JPEG", quality=85)
                    except rawpy.LibRawNoThumbnailError:
                        logger.warning(f"No thumbnail found in {record.filename}, performing basic decoding (slow).")
                        # Perform half_size extraction to save time/memory
                        rgb = raw.postprocess(half_size=True, use_camera_wb=True)
                        image = Image.fromarray(rgb)
                        image.thumbnail(PREVIEW_MAX_SIZE)
                        image.save(preview_path, "JPEG", quality=85)
            except Exception as e:
                logger.error(f"Failed to process RAW {record.filename}: {e}")
                
        elif ext in {'.jpg', '.jpeg', '.png'}:
            # Regular image, just resize to create a smaller proxy
            with Image.open(original_path) as img:
                # Convert to RGB to avoid alpha channel issues in JPEG
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail(PREVIEW_MAX_SIZE)
                img.save(preview_path, "JPEG", quality=85)
                
        if preview_path.exists():
            record.preview_path = str(preview_path)
        else:
            logger.error(f"Failed to generate preview for {record.filename}")
            
    except Exception as e:
        logger.error(f"Exception during preview generation for {record.filename}: {e}")
        
    return record

def preview_generation_module(cache_dir: Path):
    """
    Returns a callable module that takes an ImageRecord and returns an ImageRecord.
    """
    def _module(record: ImageRecord) -> ImageRecord:
        return generate_preview(record, cache_dir)
    _module.__name__ = "PreviewGeneration"
    return _module
