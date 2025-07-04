import os
from pathlib import Path
import re

def save_uploaded_file(uploaded_file, upload_dir="data/uploads", uid=None):
    """
    Save a Streamlit uploaded file to disk.
    Args:
        uploaded_file: Streamlit uploaded file object
        upload_dir: Folder to save the file into
        uid: Optional prefix (e.g., UUID for unique filenames)
    Returns:
        Full file path of saved file
    """
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    
    filename = uploaded_file.name
    # Sanitize filename to prevent path traversal
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    if uid:
        filename = f"{uid}_{filename}"
    
    file_path = os.path.join(upload_dir, filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        raise RuntimeError(f"Failed to save file: {e}")
    
    return file_path
