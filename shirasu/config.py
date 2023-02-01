import yaml
from typing import Any
from pathlib import Path
from pydantic import BaseModel


class GlobalConfig(BaseModel):
    ws: str = 'ws://127.0.0.1:8080'
    addons: dict[str, dict[str, Any]] = {}
    command_prefixes: list[str] = ['/']
    action_timeout: float = 30.


def load_config(path: str | Path) -> GlobalConfig:
    return GlobalConfig.parse_obj(yaml.safe_load(Path(path).read_text('utf8')))
