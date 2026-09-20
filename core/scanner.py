# core/scanner.py
import easyocr
import imagehash
from PIL import Image
from pathlib import Path
import cv2
from transformers import pipeline

class ImageScanner:
    def __init__(self, languages=['en', 'hi'], gpu=True):
        print("Loading OCR AI... (1/2)")
        self.reader = easyocr.Reader(languages, gpu=gpu)
        
        print("Loading Vision AI (CLIP)... (2/2) - Downloading ~600MB model on first run.")
        # device=0 uses your RTX 3050. device=-1 uses CPU.
        device = 0 if gpu else -1 
        self.classifier = pipeline(
        "zero-shot-image-classification", 
        model="openai/clip-vit-base-patch32", 
        device=device,
        model_kwargs={"use_safetensors": True} # This line bypasses the security error
    )

    def preprocess_for_ocr(self, image_path):
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError("Could not read image file.")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        width = int(gray.shape[1] * 2)
        height = int(gray.shape[0] * 2)
        enlarged = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
        adjusted = cv2.convertScaleAbs(enlarged, alpha=1.2, beta=0)
        return adjusted

    def analyze_image(self, image_path, trigger_words):
        try:
            # 1. Generate Hash
            pil_img = Image.open(image_path)
            img_hash = str(imagehash.phash(pil_img))
            
            # 2. Try OCR First 
            processed_img = self.preprocess_for_ocr(image_path)
            text_results = self.reader.readtext(processed_img, detail=0, paragraph=True)
            full_text = " ".join(text_results).lower()
            
            is_junk = any(word in full_text for word in trigger_words)
            decision_reason = f"OCR found trigger words: '{full_text}'" if is_junk else "OCR missed or found safe text."
            
            # 3. The Vision AI Fallback (If OCR didn't catch it)
            if not is_junk:
                # We ask the AI to categorize the vibe of the image
                labels = [
                    "a greeting card with a quote or wishes", 
                    "a normal photograph of people or nature", 
                    "a document or screenshot"
                ]
                # Pass the original unedited image to the Vision AI
                vision_results = self.classifier(pil_img, candidate_labels=labels)
                
                # Grab the most confident prediction
                top_result = vision_results[0] 
                
                # If it is more than 60% confident this is a greeting card, flag it!
                if top_result['label'] == "a greeting card with a quote or wishes" and top_result['score'] > 0.60:
                    is_junk = True
                    decision_reason = f"Vision AI classified as Greeting Card (Confidence: {top_result['score']*100:.1f}%)"
                    full_text = full_text + " [Vision AI Override]"

            return {
                "path": str(image_path),
                "hash": img_hash,
                "text_found": full_text,
                "is_junk": is_junk,
                "reason": decision_reason,
                "status": "success"
            }
            
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return {
                "path": str(image_path),
                "is_junk": False,
                "status": f"error: {str(e)}"
            }