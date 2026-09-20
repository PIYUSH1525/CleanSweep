# test_run.py
from core.file_manager import load_config, get_image_files
from core.scanner import ImageScanner

# Load our rules
config = load_config()
trigger_words = config["trigger_words"]
scan_dir = config["scan_directory"]

# Find images
images = get_image_files(scan_dir)
print(f"Found {len(images)} images to scan.")

# Initialize AI
scanner = ImageScanner(languages=config["languages"])

# Run the test
for img_path in images:
    result = scanner.analyze_image(img_path, trigger_words)
    print(f"\nFile: {result['path']}")
    print(f"Is Junk?: {result['is_junk']}")
    print(f"Reason: {result.get('reason', 'N/A')}") 