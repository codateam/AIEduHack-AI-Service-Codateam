from pathlib import Path
import yaml
from utils.logger import logger



def load_yaml(file_path: str):
    """Load medical configuration from YAML files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            logger.debug(f"Loading {file_path}")
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Failed to load {file_path}", exc_info=True)
        raise