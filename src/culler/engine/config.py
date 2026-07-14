import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AppConfig:
    _instance = None
    _config = {}

    @classmethod
    def load(cls, config_path: str = "config.yml"):
        path = Path(config_path)
        if path.exists():
            with open(path, "r") as f:
                cls._config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {config_path}")
        else:
            logger.warning(
                f"Configuration file {config_path} not found. Using defaults."
            )
            cls._config = {}

    @classmethod
    def get(cls, key: str, default=None):
        keys = key.split(".")
        val = cls._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val
