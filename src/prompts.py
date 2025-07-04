def get_invoice_extraction_prompt(ocr_text):
    """
    Returns a well-structured prompt to extract structured invoice fields from noisy OCR.
    """
    return f"""
    You are a helpful assistant that extracts structured fields from noisy OCR text of invoices.

    Given the following OCR-scanned invoice text, extract:

    1. **Vendor Name**
    2. **Phone Numbers** (all 10-digit mobile numbers)
    3. **Email Addresses**
    4. **GSTIN or PAN**
    5. **Invoice Table Column Headers** (list only the column names, extract row data as well)
    6. **Invoice Table Row Data** (extract all the row data)
    7. **Invoice Table Size/Dimensions** (extract the number of rows and columns)
    8. **Invoice Scanned Or Not** (scanned or digital)
    9. **Invoice Format Type** (handwritten or typed or mixed)

    Return the result strictly as a JSON object like this (if the table is not present, set 'table_size', 'table_headers', and 'table_row_data' to null or empty lists):

    {{
      "vendor_name": "XYZ Pvt Ltd",
      "phone_numbers": ["1234567890", "9876543210"],
      "email_addresses": ["example@email.com"],
      "gst_or_pan": "ABCDE1234F",
      "table_headers": ["Description", "Qty", "Rate", "Amount"],
      "table_row_data": [["Item 1", "1", "100", "100"], ["Item 2", "2", "200", "400"]],
      "table_size": {{"rows": 2, "columns": 4}} if the table is present else None,
      "scanned_or_typed": "scanned",
      "handwritten_or_typed": "typed"
    }}

    OCR Text:
    {ocr_text}
"""
