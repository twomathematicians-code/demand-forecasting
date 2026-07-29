import logging, sys

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
