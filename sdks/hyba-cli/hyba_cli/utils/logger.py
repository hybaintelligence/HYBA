"""
Logging setup for HYBA CLI
"""

import logging
from pathlib import Path


def setup_logging(debug: bool = False):
    """Setup logging for HYBA CLI"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Log file
    log_dir = Path.home() / ".hyba"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "hyba.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler() if debug else logging.NullHandler(),
        ]
    )
    
    return logging.getLogger(__name__)
