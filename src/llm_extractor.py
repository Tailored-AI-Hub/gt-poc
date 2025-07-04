import os
from openai import OpenAI
from dotenv import load_dotenv

from src.prompts import get_invoice_extraction_prompt
from src.extractor import extract_images_from_file

import base64

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def extract_invoice_fields_with_llm(ocr_text, image_paths=None, model="gpt-4o", temperature=0.1):
    """
    Extract structured fields from noisy OCR using OpenAI LLM with vision.
    Returns: dict with vendor, phone, email, table_headers, and summary.
    """
    if image_paths is None:
        image_paths = []

    prompt = get_invoice_extraction_prompt(ocr_text)

    # Prepare vision message content
    content = [
        {"type": "text", "text": prompt}
    ]
    for img_path in image_paths:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{encode_image_to_base64(img_path)}"
            }
        })

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an intelligent OCR cleanup and data extraction assistant."},
                {"role": "user", "content": content}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        result_text = response.choices[0].message.content
    except Exception as e:
        return {"error": f"OpenAI API error: {e}", "raw_output": ""}

    # Try parsing JSON-like output
    try:
        import json
        parsed = json.loads(result_text)
    except Exception as e:
        parsed = {"error": "LLM returned unstructured text", "raw_output": result_text}

    return parsed
