import os
from pathlib import Path
import re
from src.logger_config import get_logger

logger = get_logger(__name__)

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
    logger.debug(f"Saving uploaded file: {uploaded_file.name} to {upload_dir}")
    
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created/verified upload directory: {upload_dir}")
    
    filename = uploaded_file.name
    # Sanitize filename to prevent path traversal
    original_filename = filename
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    if uid:
        filename = f"{uid}_{filename}"
    
    if original_filename != filename:
        logger.warning(f"Filename sanitized: '{original_filename}' -> '{filename}'")
    
    file_path = os.path.join(upload_dir, filename)
    logger.debug(f"Full file path: {file_path}")
    
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logger.info(f"File saved successfully: {file_path} ({uploaded_file.size} bytes)")
    except Exception as e:
        logger.error(f"Failed to save file {uploaded_file.name}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to save file: {e}")
    
    return file_path
