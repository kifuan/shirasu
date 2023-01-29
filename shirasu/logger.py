import sys
from loguru import logger as logger


logger.configure(
    handlers=[{
        'sink': sys.stdout,
        'format': '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
                  '<level>{level: <8}</level> | '
                  '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
                  '<level>{message}</level>'
    }]
)
