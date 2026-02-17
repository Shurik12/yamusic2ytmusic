import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Config loaded from {config_path}")
            return config
    except FileNotFoundError:
        logger.error(f"Config file {config_path} not found!")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing {config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        raise