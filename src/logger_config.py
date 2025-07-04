import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name, log_level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for detailed logs
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(f'logs/{name.replace(".", "_")}_{today}.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name):
    """
    Get a logger instance for the given name.
    """
    return setup_logger(name)

def set_log_level(level_name):
    """
    Set the global log level.
    
    Args:
        level_name: Log level name ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    if level_name.upper() in level_map:
        logging.getLogger().setLevel(level_map[level_name.upper()])
        print(f"Log level set to: {level_name.upper()}")
    else:
        print(f"Invalid log level: {level_name}. Valid levels: {list(level_map.keys())}")

def log_function_call(func):
    """
    Decorator to log function calls with parameters and return values.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised exception: {e}", exc_info=True)
            raise
    
    return wrapper

def log_execution_time(func):
    """
    Decorator to log function execution time.
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}", exc_info=True)
            raise
    
    return wrapper

def cleanup_old_logs(days_to_keep=30):
    """
    Clean up log files older than specified days.
    
    Args:
        days_to_keep: Number of days to keep log files (default: 30)
    """
    import time
    from datetime import timedelta
    
    logger = get_logger(__name__)
    log_dir = Path("logs")
    
    if not log_dir.exists():
        logger.info("Logs directory doesn't exist, nothing to clean up")
        return
    
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    deleted_count = 0
    
    for log_file in log_dir.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old log file: {log_file}")
            except Exception as e:
                logger.warning(f"Failed to delete old log file {log_file}: {e}")
    
    logger.info(f"Log cleanup completed: {deleted_count} old files deleted")

def get_log_stats():
    """
    Get statistics about log files.
    
    Returns:
        dict: Statistics about log files
    """
    log_dir = Path("logs")
    
    if not log_dir.exists():
        return {"total_files": 0, "total_size": 0, "files": []}
    
    stats = {
        "total_files": 0,
        "total_size": 0,
        "files": []
    }
    
    for log_file in log_dir.glob("*.log"):
        try:
            file_size = log_file.stat().st_size
            stats["total_files"] += 1
            stats["total_size"] += file_size
            stats["files"].append({
                "name": log_file.name,
                "size": file_size,
                "modified": datetime.fromtimestamp(log_file.stat().st_mtime)
            })
        except Exception as e:
            print(f"Error reading log file {log_file}: {e}")
    
    return stats

# Example usage and testing
if __name__ == "__main__":
    # Test the logging setup
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test log statistics
    stats = get_log_stats()
    print(f"Log statistics: {stats}")
    
    # Test log cleanup (uncomment to test)
    # cleanup_old_logs(days_to_keep=1)
