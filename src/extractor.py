import os
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import tempfile
from pathlib import Path

def process_file_ocr(file_path):
    """
    Given a PDF or image file, return extracted OCR text.
    If PDF, convert pages to images first.
    """
    file_ext = Path(file_path).suffix.lower()
    ocr_text = ""

    if file_ext == ".pdf":
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(file_path, dpi=300, output_folder=temp_dir)
                for i, img in enumerate(images):
                    text = pytesseract.image_to_string(img)
                    ocr_text += f"\n\n--- Page {i+1} ---\n\n{text}"
        except Exception as e:
            return {"ocr_text": f"[PDF OCR failed: {e}]"}
    elif file_ext in [".jpg", ".jpeg", ".png"]:
        try:
            img = Image.open(file_path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            ocr_text = pytesseract.image_to_string(img)
        except Exception as e:
            ocr_text = f"[Image OCR failed: {e}]"
    else:
        ocr_text = "[Unsupported file type]"

    return {
        "ocr_text": ocr_text.strip()
    }

def extract_images_from_file(file_path):
    """
    Given a PDF or image file, return a list of image file paths (one per page for PDFs, or the image itself).
    PDF page images are saved to a persistent directory (data/uploads/pages/).
    """
    file_ext = Path(file_path).suffix.lower()
    image_paths = []
    persistent_dir = os.path.join("data", "uploads", "pages")
    os.makedirs(persistent_dir, exist_ok=True)
    base_name = Path(file_path).stem

    if file_ext == ".pdf":
        try:
            images = convert_from_path(file_path, dpi=300)
            for i, img in enumerate(images):
                img_path = os.path.join(persistent_dir, f"{base_name}_page_{i+1}.png")
                img.save(img_path, "PNG")
                image_paths.append(img_path)
            return image_paths
        except Exception as e:
            return []
    elif file_ext in [".jpg", ".jpeg", ".png"]:
        image_paths.append(file_path)
    return image_paths

def cleanup_images(image_paths):
    """
    Delete the image files at the given paths.
    """
    for img_path in image_paths:
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
        except Exception:
            pass
