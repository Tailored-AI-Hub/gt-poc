import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import openai
from .logger_config import get_logger

from src.prompts import get_invoice_extraction_prompt
from src.extractor import extract_images_from_file

import base64

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = get_logger(__name__)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def extract_invoice_fields_with_llm(ocr_text, image_paths=None):
    """
    Extract structured invoice fields using LLM.
    """
    logger.info("Starting LLM-based invoice field extraction")
    logger.debug(f"OCR text length: {len(ocr_text)} characters")
    logger.debug(f"Number of images: {len(image_paths) if image_paths else 0}")
    
    try:
        # Prepare the prompt
        prompt = get_invoice_extraction_prompt(ocr_text)
        logger.debug("Prompt prepared successfully")
        
        # Call OpenAI API
        logger.debug("Calling OpenAI API")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert invoice analyzer. Extract structured data from invoices accurately."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        logger.debug("OpenAI API call completed successfully")
        
        # Parse the response
        content = response.choices[0].message.content
        logger.debug(f"Raw LLM response length: {len(content)} characters")
        
        try:
            # Try to parse as JSON
            structured_data = json.loads(content)
            logger.info("Successfully parsed LLM response as JSON")
            logger.debug(f"Extracted fields: {list(structured_data.keys())}")
            
            return structured_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response content: {content}")
            
            return {
                "error": f"Failed to parse LLM response: {e}",
                "raw_output": content
            }
            
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}", exc_info=True)
        return {
            "error": f"LLM extraction failed: {e}",
            "raw_output": ""
        }
