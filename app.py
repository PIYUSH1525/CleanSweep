# app.py
import streamlit as st
import os
from PIL import Image
from core.file_manager import load_config, get_image_files, safe_delete
from core.scanner import ImageScanner

# Set page layout
st.set_page_config(page_title="WhatsApp Junk Cleaner", page_icon="🧹", layout="wide")

# 1. LOAD AI SAFELY: This decorator ensures the AI only loads ONCE per session
@st.cache_resource(show_spinner="Loading AI Models into memory...")
def load_ai(languages, gpu):
    return ImageScanner(languages=languages, gpu=gpu)

# 2. LOAD CONFIG
config = load_config()
trigger_words = config.get("trigger_words", [])
default_dir = config.get("scan_directory", "./sample_data")

# 3. UI HEADER
st.title("🧹 WhatsApp Media Cleaner")
st.markdown("Scan your folders for annoying Good Morning/Greeting messages and delete them safely.")

# Initialize session state to store flagged images between clicks
if 'flagged_images' not in st.session_state:
    st.session_state.flagged_images = []

# 4. SIDEBAR CONTROLS
st.sidebar.header("Scan Settings")
scan_dir = st.sidebar.text_input("Folder to Scan", value=default_dir)

if st.sidebar.button("Start Scan", type="primary"):
    images = get_image_files(scan_dir)
    if not images:
        st.sidebar.error(f"No images found in {scan_dir}")
    else:
        # Load AI
        scanner = load_ai(config["languages"], gpu=True)
        st.session_state.flagged_images = [] # Reset previous results
        
        # Setup Progress Bar
        progress_bar = st.progress(0, text="Starting scan...")
        
        # Scan loop
        for i, img_path in enumerate(images):
            # Update progress UI
            progress = (i + 1) / len(images)
            progress_bar.progress(progress, text=f"Scanning: {i+1} / {len(images)} files")
            
            # Analyze
            result = scanner.analyze_image(img_path, trigger_words)
            if result.get("is_junk"):
                st.session_state.flagged_images.append(result)
                
        progress_bar.empty()
        st.success(f"Scan complete! Found {len(st.session_state.flagged_images)} junk images.")

# 5. REVIEW & DELETE UI
if st.session_state.flagged_images:
    st.divider()
    st.subheader("🗑️ Review & Clean")
    st.markdown("Uncheck any images you want to keep. The rest will be moved to the Recycle Bin.")
    
    # We use a form so the page doesn't glitch while checking multiple boxes
    with st.form("delete_form"):
        cols = st.columns(3) # Display 3 images per row
        to_delete = {}
        
        for index, item in enumerate(st.session_state.flagged_images):
            col = cols[index % 3]
            with col:
                try:
                    img = Image.open(item["path"])
                    st.image(img, use_container_width=True)
                    st.caption(f"**Reason:** {item.get('reason', 'N/A')}")
                    # Checkbox defaults to True (checked for deletion)
                    file_name = os.path.basename(item["path"])
                    to_delete[item["path"]] = st.checkbox(f"Delete {file_name}", value=True, key=item["path"])
                except Exception as e:
                    st.error(f"Error loading image preview: {e}")
        
        submit_btn = st.form_submit_button("Move Selected to Recycle Bin", type="primary")
        
        if submit_btn:
            deleted_count = 0
            for path, should_delete in to_delete.items():
                if should_delete:
                    if safe_delete(path):
                        deleted_count += 1
            
            st.success(f"Successfully moved {deleted_count} images to the Recycle Bin! ♻️")
            st.session_state.flagged_images = [] # Clear the grid
            st.rerun() # Refresh the page instantly