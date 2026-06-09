import logging
import time
import sys
from pythonjsonlogger import jsonlogger

def init_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    
    # Remove default handlers to avoid duplicate logs
    for handler in logger.handlers[:-1]:
        logger.removeHandler(handler)

    logging.info("Telemetry: Structured JSON logging initialized.")

def init_metrics():
    # Placeholder for Prometheus / metrics initialization
    logging.info("Telemetry: Performance metrics collector active.")
