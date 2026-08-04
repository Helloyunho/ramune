import logging
import time
from pathlib import Path

CONSOLE_LEVEL = logging.INFO
FILE_LEVEL = logging.DEBUG


LOGS_DIR = Path("logs")


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(min(CONSOLE_LEVEL, FILE_LEVEL))
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(CONSOLE_LEVEL)
        logger.addHandler(console_handler)
        LOGS_DIR.mkdir(exist_ok=True)
        existing_log_files = list(LOGS_DIR.glob(f"*{name}.log"))
        for log_file in existing_log_files:
            timestamp = int(log_file.stem.split("-")[0])
            if (
                time.time_ns() // 1000 - timestamp > 7 * 24 * 60 * 60 * 1000000
            ):  # 7 days in microseconds
                log_file.unlink()
        file_handler = logging.FileHandler(
            LOGS_DIR / f"{time.time_ns()//1000}-{name}.log"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(FILE_LEVEL)
        logger.addHandler(file_handler)
    return logger
