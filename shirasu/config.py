from typing import Any
from pathlib import Path
from pydantic import BaseModel


class Config(BaseModel):
    ws: str = 'ws://127.0.0.1:8080'
    addons: dict[str, dict[str, Any]] = {}
    command_start: list[str] = ['/']


def load_config(path: str | Path) -> Config:
    return Config.parse_file(path)
