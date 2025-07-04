from difflib import SequenceMatcher

def structural_fingerprint(headers, format_style, table_size=None, handwritten_or_typed=None):
    """
    Create a simplified fingerprint of invoice layout using:
    - table headers (joined with spacing logic)
    - format type (typed, scanned, etc.)
    - table size (rows x columns)
    - handwritten or typed
    Returns a string representation
    """
    if not headers:
        layout_string = format_style or "unknown"
    else:
        layout_string = " | ".join(header.lower() for header in headers)
    size_string = f"{table_size.get('rows','?')}x{table_size.get('columns','?')}" if isinstance(table_size, dict) else "?x?"
    hw_string = handwritten_or_typed or "unknown"
    fingerprint = f"{format_style}::{layout_string}::{size_string}::{hw_string}"
    return fingerprint

def layout_similarity(f1, f2):
    """
    Compute similarity between two layout fingerprints.
    Uses SequenceMatcher ratio (string-level comparison).
    Returns: float between 0 and 1
    """
    return SequenceMatcher(None, f1, f2).ratio()

def are_layouts_similar(headers1, headers2, format1, format2, table_size1=None, table_size2=None, handwritten1=None, handwritten2=None, threshold=0.85):
    """
    Wrapper to compare structural layout fingerprints, now including table size and handwritten/typed.
    Returns: (bool, similarity_score)
    """
    fp1 = structural_fingerprint(headers1, format1, table_size1, handwritten1)
    fp2 = structural_fingerprint(headers2, format2, table_size2, handwritten2)
    sim = layout_similarity(fp1, fp2)
    return sim >= threshold, sim
