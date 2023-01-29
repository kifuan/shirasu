import sys
from loguru import Logger
from loguru import logger as logger


logger.configure(
    handlers=[{
        'sink': sys.stdout,
        'format': '<green>{time:YY-MM-DD HH:mm:ss}</green> | '
                  '<level>{level: <8}</level> | '
                  '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
                  '<level>{message}</level>'
    }]
)


def logger_with_func_name(name: str) -> Logger:
    return logger.patch(lambda r: r.update(function=name))  # type: ignore[call-arg]
