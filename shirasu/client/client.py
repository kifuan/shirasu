import abc
from typing import Any


class Client(abc.ABC):
    @abc.abstractmethod
    async def call_action(self, action: str, **params: Any) -> dict[str, Any]:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    async def listen(cls, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError()
