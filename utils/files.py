import os
import json
from loguru import logger

def load_json(file_path):
    """Safely loads data from a JSON file."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return []

def save_json(data, file_path):
    """Saves data to a JSON file with pretty formatting."""
    try:
        ensure_dir(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")

def ensure_dir(directory):
    """Ensures that a directory exists."""
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
