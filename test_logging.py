#!/usr/bin/env python3
"""
Test script to verify logging setup is working correctly.
"""

from src.logger_config import get_logger

def test_logging():
    """Test all logging levels."""
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("Logging test completed. Check the logs/ directory for log files.")

if __name__ == "__main__":
    test_logging() 