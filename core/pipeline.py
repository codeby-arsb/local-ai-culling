import logging
from typing import List, Callable
from .models import ImageRecord, ClassificationType

logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self):
        # A module is just a callable that takes an ImageRecord and returns an ImageRecord
        self.modules: List[Callable[[ImageRecord], ImageRecord]] = []
        
    def add_module(self, module_func: Callable[[ImageRecord], ImageRecord]):
        """Adds a processing module to the pipeline."""
        self.modules.append(module_func)
        
    def process(self, image_record: ImageRecord) -> ImageRecord:
        """Runs the image record through all modules."""
        logger.debug(f"Processing {image_record.filename}")
        import time
        import cv2
        start_t = time.perf_counter()
        
        # Transient Image Caching
        if image_record.preview_path:
            try:
                img_bgr = cv2.imread(image_record.preview_path)
                if img_bgr is not None:
                    image_record.image_bgr = img_bgr
                    image_record.image_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            except Exception as e:
                logger.error(f"Failed to load cache image {image_record.preview_path}: {e}")
        
        for module in self.modules:
            module_name = module.__name__ if hasattr(module, '__name__') else str(module.__class__.__name__)
            try:
                # Modules should modify the record in place or return the updated record
                image_record = module(image_record)
            except Exception as e:
                import traceback
                logger.error(f"Module '{module_name}' failed on '{image_record.filename}'. Reason: {e}")
                logger.debug(traceback.format_exc())
                image_record.classification = ClassificationType.REVIEW
                image_record.classification_reasons.append(f"Pipeline error in {module_name}: {str(e)}")
                
        # Release Transient Images
        image_record.image_bgr = None
        image_record.image_gray = None
                
        end_t = time.perf_counter()
        image_record.processing_time_ms = (end_t - start_t) * 1000.0
        return image_record
        
    def process_batch(self, image_records: List[ImageRecord]) -> List[ImageRecord]:
        """Processes a batch of records."""
        return [self.process(record) for record in image_records]
