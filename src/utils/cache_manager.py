import os
import hashlib
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT_DIR / "parent_store" / "processed_files.json"

def get_file_hash(file_path):
    """Calculate MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_cache_registry():
    """Load the processed files registry."""
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        return {}
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def update_cache_registry(filename, file_hash):
    """Update the processed files registry."""
    registry = get_cache_registry()
    registry[filename] = file_hash
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

def is_file_processed(filename, file_hash):
    """Check if a file with the given name and hash has already been processed."""
    registry = get_cache_registry()
    return registry.get(filename) == file_hash

def clear_cache():
    """Clear the cache registry."""
    if REGISTRY_PATH.exists():
        os.remove(REGISTRY_PATH)
