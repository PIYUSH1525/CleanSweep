# core/scanner.py
import easyocr
import imagehash
from PIL import Image
from pathlib import Path

class ImageScanner:
    def __init__(self, languages=['en', 'hi'], gpu=False):
        """Initializes the OCR reader. Loads models into memory."""
        print(f"Loading OCR AI for {languages}... This might take a moment.")
        # gpu=False keeps it free and compatible with any basic laptop CPU
        self.reader = easyocr.Reader(languages, gpu=gpu)

    def analyze_image(self, image_path, trigger_words):
        """Scans a single image for text and generates a duplicate-detection hash."""
        try:
            # 1. Generate Perceptual Hash (for exact duplicates later)
            img = Image.open(image_path)
            img_hash = str(imagehash.phash(img))
            
            # 2. Extract Text (detail=0 returns just the string arrays)
            text_results = self.reader.readtext(str(image_path), detail=0)
            
            # Combine all found text into one lowercase string for easy matching
            full_text = " ".join(text_results).lower()
            
            # 3. Check against trigger words from our config
            is_junk = any(word in full_text for word in trigger_words)
            
            return {
                "path": str(image_path),
                "hash": img_hash,
                "text_found": full_text,
                "is_junk": is_junk,
                "status": "success"
            }
            
        except Exception as e:
            # Catch corrupted images or unreadable files so the loop doesn't crash
            print(f"Error processing {image_path}: {e}")
            return {
                "path": str(image_path),
                "is_junk": False,
                "status": f"error: {str(e)}"
            }