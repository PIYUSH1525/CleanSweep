# core/file_manager.py
import json
from pathlib import Path
from send2trash import send2trash

def load_config(config_path="config.json"):
    """Loads the settings and trigger words from config.json"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found. Please create it.")
        return None

def get_image_files(directory):
    """Scans the directory for image files and removes duplicates."""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"Directory {directory} does not exist.")
        return []
    
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp']
    images = set() # Using a Set automatically removes duplicates!
    
    for ext in extensions:
        # We convert to absolute paths (.resolve()) to ensure the Set catches them
        for p in dir_path.rglob(ext):
            images.add(p.resolve())
        for p in dir_path.rglob(ext.upper()):
            images.add(p.resolve())
        
    return list(images)

def safe_delete(file_path):
    """Moves the file to the Windows Recycle Bin instead of permanent deletion."""
    try:
        # Resolve gets the absolute, correct Windows path
        absolute_path = str(Path(file_path).resolve())
        send2trash(absolute_path)
        return True
    except Exception as e:
        print(f"Failed to trash {file_path}: {e}")
        return False 