from difflib import SequenceMatcher
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .logger_config import get_logger

logger = get_logger(__name__)

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

def are_layouts_similar(headers1, headers2, scanned1, scanned2, table_size1, table_size2, handwritten1, handwritten2):
    """
    Compare two invoice layouts for similarity.
    """
    logger.debug(f"Comparing layouts: {len(headers1)} vs {len(headers2)} headers")
    
    try:
        # Basic similarity checks
        if scanned1 != scanned2:
            logger.debug("Different scan types detected")
            return False, 0.0
        
        if handwritten1 != handwritten2:
            logger.debug("Different handwriting types detected")
            return False, 0.0
        
        # Compare table sizes if available
        if table_size1 and table_size2:
            size_diff = abs(table_size1 - table_size2) / max(table_size1, table_size2)
            if size_diff > 0.3:  # More than 30% difference
                logger.debug(f"Table sizes too different: {table_size1} vs {table_size2}")
                return False, 0.0
        
        # Compare headers using TF-IDF
        if not headers1 or not headers2:
            logger.debug("Empty headers detected")
            return False, 0.0
        
        # Convert headers to text for comparison
        text1 = " ".join(headers1)
        text2 = " ".join(headers2)
        
        logger.debug(f"Header text 1: {text1[:100]}...")
        logger.debug(f"Header text 2: {text2[:100]}...")
        
        # Use TF-IDF for similarity
        vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            logger.debug(f"Layout similarity score: {similarity:.3f}")
            return similarity > 0.7, similarity
            
        except Exception as e:
            logger.warning(f"TF-IDF comparison failed: {e}")
            # Fallback to simple string comparison
            common_words = set(text1.lower().split()) & set(text2.lower().split())
            total_words = set(text1.lower().split()) | set(text2.lower().split())
            similarity = len(common_words) / len(total_words) if total_words else 0.0
            
            logger.debug(f"Fallback similarity score: {similarity:.3f}")
            return similarity > 0.5, similarity
            
    except Exception as e:
        logger.error(f"Layout comparison failed: {e}", exc_info=True)
        return False, 0.0
