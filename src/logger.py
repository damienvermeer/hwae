"""
HWAE (Hostile Waters Antaeus Eternal)

logger.py

Custom logger for the HWAE application that logs to both console and a CSV file
"""

import logging
import csv
import os
import datetime
from pathlib import Path

from src.constants import LOGGER_NAME


class CsvFormatter(logging.Formatter):
    """Custom formatter that formats log records as CSV rows"""

    def format(self, record):
        """Format the log record as a CSV row"""
        timestamp = datetime.datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        recordtxt = record.getMessage().replace(",", ";")
        return f"{timestamp},{record.levelname},{recordtxt}"


class CsvHandler(logging.FileHandler):
    """Custom handler for logging to a CSV file"""

    def __init__(self, filename, mode="a", encoding=None, delay=False):
        """Initialize the handler with the CSV file"""
        super().__init__(filename, mode, encoding, delay)

        # Create CSV file with header if it doesn't exist or is empty
        if not Path(filename).exists() or Path(filename).stat().st_size == 0:
            with open(filename, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Level", "Message"])

        self.setFormatter(CsvFormatter())


def setup_logger(output_path=None):
    """Set up the HWAE logger

    Args:
        output_path (Path, optional): Path to the output directory for the CSV log file.
            If None, no CSV file will be created.

    Returns:
        logging.Logger: The configured logger
    """
    # Get the logger
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Add CSV handler if output path is provided
    if output_path:
        # Ensure the directory exists
        Path(output_path).mkdir(parents=True, exist_ok=True)

        # if the logging file exists, remove it (so we get one log)
        logpath = Path(output_path) / "hwae_log.csv"
        if logpath.exists():
            logpath.unlink()

        # Create the CSV handler
        csv_handler = CsvHandler(logpath)
        logger.addHandler(csv_handler)

    return logger


def get_logger():
    """Get the HWAE logger

    Returns:
        logging.Logger: The HWAE logger
    """
    return logging.getLogger(LOGGER_NAME)


def close_logger():
    """Close all handlers for the HWAE logger to release file locks"""
    logger = logging.getLogger(LOGGER_NAME)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
