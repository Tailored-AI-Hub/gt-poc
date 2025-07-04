from .logger_config import get_logger

logger = get_logger(__name__)

def get_invoice_extraction_prompt(ocr_text):
    """
    Generate the prompt for invoice field extraction.
    """
    logger.debug("Generating invoice extraction prompt")
    
    prompt = f"""
    Analyze the following invoice text and extract structured information. Return the result as a valid JSON object with the following fields:

    {{
        "vendor_name": "Name of the vendor/company",
        "phone_numbers": ["list", "of", "phone", "numbers"],
        "email_addresses": ["list", "of", "email", "addresses"],
        "gst_or_pan": "GST number or PAN number if found",
        "table_headers": ["list", "of", "table", "column", "headers"],
        "table_row_data": [["row1", "data"], ["row2", "data"]],
        "table_size": number_of_rows_in_table,
        "scanned_or_typed": "scanned" or "typed",
        "handwritten_or_typed": "handwritten" or "typed"
    }}

    Invoice Text:
    {ocr_text[:3000]}

    Instructions:
    1. Extract all phone numbers and email addresses
    2. Identify table headers and data
    3. Determine if the document is scanned or typed
    4. Determine if text is handwritten or typed
    5. Return only valid JSON, no additional text
    """
    
    logger.debug(f"Prompt generated with {len(prompt)} characters")
    return prompt
