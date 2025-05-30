import os
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

# Define log format
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Determine if we're running in Vercel
IS_VERCEL = os.getenv("VERCEL") == "1"

# Remove any existing default logger configurations
logger.remove()

# Always log to stderr (Vercel captures this)
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format=LOG_FORMAT,
    enqueue=True,
    backtrace=True,
    diagnose=True
)

# Add file logging ONLY for local development
if not IS_VERCEL:
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app.log",
        rotation="10 MB",
        retention="10 days",
        level=settings.LOG_LEVEL,
        format=LOG_FORMAT,
        enqueue=True,
        backtrace=True,
        diagnose=True
    )
    logger.info("File logging enabled")
else:
    logger.info("Running in Vercel environment - file logging disabled")