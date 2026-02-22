"""
Centralized logging setup for the entire project.
Configures handlers, formatters, and loggers from YAML config.
"""

import logging
import logging.config
import yaml
import os
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Get the project root directory (3 levels up from this file).
    
    File structure:
        project_root/
        └── src/
            └── utils/
                └── logger.py  (this file)
    
    Returns:
        Path: Absolute path to project root
    """
    return Path(__file__).resolve().parent.parent.parent


def setup_logging(config_path: Optional[str] = None, 
                 fallback_level: int = logging.INFO) -> None:
    """
    Setup logging configuration from YAML file with fallback.
    
    Args:
        config_path: Path to logging.yml. If None, uses default location.
        fallback_level: Logging level to use if config file not found.
    
    Raises:
        None: Always succeeds, falls back to basic config if needed.
    """
    project_root = get_project_root()
    
    # Default config path
    if config_path is None:
        config_path = project_root / "config" / "logging.yml"
    else:
        config_path = Path(config_path)
    
    # Check if config file exists
    if not config_path.exists():
        _setup_fallback_logging(fallback_level)
        logging.warning(f"Logging config not found at {config_path}, using fallback configuration")
        return
    
    # Load YAML config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        _setup_fallback_logging(fallback_level)
        logging.error(f"Failed to parse logging config: {e}")
        return
    except Exception as e:
        _setup_fallback_logging(fallback_level)
        logging.error(f"Unexpected error loading logging config: {e}")
        return
    
    # Ensure log directories exist
    _ensure_log_directories(config, project_root)
    
    # Apply logging configuration
    try:
        logging.config.dictConfig(config)
        logging.getLogger("root").info(f"Logging system initialized from {config_path}")
    except Exception as e:
        _setup_fallback_logging(fallback_level)
        logging.error(f"Failed to configure logging: {e}")


def _ensure_log_directories(config: dict, project_root: Path) -> None:
    """
    Create log directories for all file handlers.
    
    Args:
        config: Logging configuration dictionary
        project_root: Project root directory
    """
    handlers = config.get("handlers", {})
    
    for handler_name, handler_config in handlers.items():
        if "filename" in handler_config:
            # Convert relative path to absolute
            log_file = project_root / handler_config["filename"]
            
            # Update config with absolute path
            handler_config["filename"] = str(log_file)
            
            # Create parent directory
            log_file.parent.mkdir(parents=True, exist_ok=True)


def _setup_fallback_logging(level: int = logging.INFO) -> None:
    """
    Setup basic logging configuration as fallback.
    
    Args:
        level: Logging level (default: INFO)
    """
    project_root = get_project_root()
    fallback_log = project_root / "logs" / "fallback.log"
    
    # Ensure logs directory exists
    fallback_log.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure basic logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(fallback_log, encoding='utf-8')
        ]
    )
    
    logging.warning("Using fallback logging configuration")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Convenience function to get logger after setup_logging() has been called.
    
    Args:
        name: Logger name (typically __name__ or class name)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


# Convenience function for testing
def reset_logging() -> None:
    """
    Reset logging configuration.
    
    Useful for testing or when you need to reconfigure logging.
    """
    # Remove all handlers from all loggers
    loggers = [logging.getLogger()] + [
        logging.getLogger(name) for name in logging.root.manager.loggerDict
    ]
    
    for logger in loggers:
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)


if __name__ == "__main__":
    """Test the logging setup"""
    
    # Test with default config
    print("Testing logging setup...")
    setup_logging()
    
    # Test different loggers
    test_logger = get_logger("test_module")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    
    # Test scraper logger
    scraper_logger = get_logger("src.pipelines.general_scraper")
    scraper_logger.debug("Scraper debug message")
    scraper_logger.info("Scraper info message")
    
    print("\nCheck logs/ directory for output files")