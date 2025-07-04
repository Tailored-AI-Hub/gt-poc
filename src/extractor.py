import os
import fitz  # PyMuPDF
from PIL import Image
import io
from .logger_config import get_logger

logger = get_logger(__name__)

def process_file_ocr(file_path):
    """
    Process a file (PDF or image) and extract text using OCR.
    """
    logger.info(f"Starting OCR processing for file: {file_path}")
    
    try:
        if file_path.lower().endswith('.pdf'):
            logger.debug("Processing PDF file")
            return process_pdf_ocr(file_path)
        else:
            logger.debug("Processing image file")
            return process_image_ocr(file_path)
    except Exception as e:
        logger.error(f"OCR processing failed for {file_path}: {e}", exc_info=True)
        raise

def process_pdf_ocr(file_path):
    """Extract text from PDF using PyMuPDF."""
    logger.debug(f"Extracting text from PDF: {file_path}")
    
    try:
        doc = fitz.open(file_path)
        logger.debug(f"PDF opened successfully, {len(doc)} pages")
        
        text_content = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            text_content.append(text)
            logger.debug(f"Extracted text from page {page_num + 1}: {len(text)} characters")
        
        doc.close()
        
        full_text = "\n".join(text_content)
        logger.info(f"PDF OCR completed: {len(full_text)} total characters extracted")
        
        return {
            "ocr_text": full_text,
            "page_count": len(doc),
            "file_type": "pdf"
        }
        
    except Exception as e:
        logger.error(f"PDF OCR failed for {file_path}: {e}", exc_info=True)
        raise

def process_image_ocr(file_path):
    """Extract text from image using OCR (placeholder for now)."""
    logger.debug(f"Processing image OCR for: {file_path}")
    
    # Placeholder - you would integrate with an OCR service here
    logger.warning("Image OCR not implemented yet - returning placeholder")
    
    return {
        "ocr_text": "Image OCR not implemented",
        "page_count": 1,
        "file_type": "image"
    }

def extract_images_from_file(file_path):
    """Extract images from PDF file."""
    logger.debug(f"Extracting images from file: {file_path}")
    
    if not file_path.lower().endswith('.pdf'):
        logger.debug("Not a PDF file, skipping image extraction")
        return []
    
    try:
        doc = fitz.open(file_path)
        image_paths = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                    else:  # CMYK: convert to RGB first
                        pix1 = fitz.Pixmap(fitz.csRGB, pix)
                        img_data = pix1.tobytes("png")
                        pix1 = None
                    
                    # Save image
                    img_filename = f"extracted_image_{page_num}_{img_index}.png"
                    img_path = os.path.join("temp", img_filename)
                    os.makedirs("temp", exist_ok=True)
                    
                    with open(img_path, "wb") as img_file:
                        img_file.write(img_data)
                    
                    image_paths.append(img_path)
                    logger.debug(f"Extracted image: {img_path}")
                    
                    pix = None
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                    continue
        
        doc.close()
        logger.info(f"Image extraction completed: {len(image_paths)} images extracted")
        return image_paths
        
    except Exception as e:
        logger.error(f"Image extraction failed for {file_path}: {e}", exc_info=True)
        return []

def cleanup_images(image_paths):
    """Clean up extracted image files."""
    logger.debug(f"Cleaning up {len(image_paths)} extracted images")
    
    for img_path in image_paths:
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
                logger.debug(f"Removed image: {img_path}")
        except Exception as e:
            logger.warning(f"Failed to remove image {img_path}: {e}")
    
    logger.info("Image cleanup completed")
