import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: Path, max_size_mb: float = 500.0):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024

    def enforce_limits(self):
        """Monitors and cleans the preview cache if it exceeds the max size."""
        if not self.cache_dir.exists() or not self.cache_dir.is_dir():
            logger.debug("Cache directory does not exist. Nothing to enforce.")
            return

        files = [f for f in self.cache_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']]

        # Calculate total size
        total_size = sum(f.stat().st_size for f in files)
        
        if total_size <= self.max_size_bytes:
            logger.info(f"Cache size is {total_size / (1024*1024):.2f} MB. Limit: {self.max_size_bytes / (1024*1024):.2f} MB. No cleanup needed.")
            return

        logger.info(f"Cache size {total_size / (1024*1024):.2f} MB exceeds limit {self.max_size_bytes / (1024*1024):.2f} MB. Initiating cleanup...")

        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x.stat().st_mtime)

        freed_space = 0
        deleted_count = 0
        
        for f in files:
            size = f.stat().st_size
            try:
                f.unlink()
                freed_space += size
                total_size -= size
                deleted_count += 1
                if total_size <= self.max_size_bytes:
                    break
            except Exception as e:
                logger.error(f"Failed to delete cached preview {f}: {e}")

        logger.info(f"Cache cleanup complete. Deleted {deleted_count} files, freed {freed_space / (1024*1024):.2f} MB. New size: {total_size / (1024*1024):.2f} MB.")
