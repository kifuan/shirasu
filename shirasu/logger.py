import sys
from typing import TYPE_CHECKING, Any
from loguru import logger as logger

if TYPE_CHECKING:
    from loguru import Logger


logger.configure(
    handlers=[{
        'sink': sys.stdout,
        'level': 'DEBUG',
        'format': '<green>{time:YY-MM-DD HH:mm:ss}</green> | '
                  '<level>{level: <8}</level> | '
                  '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
                  '<level>{message}</level>',
    }]
)


def logger_deco(f: Any) -> "Logger":
    return logger.patch(lambda r: r.update(
        function=f.__name__,
        name=f.__module__,
        line=f.__code__.co_firstlineno,
    ))  # type: ignore[call-arg]
