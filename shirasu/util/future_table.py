import sys
import asyncio
from typing import Any


class FutureTable:
    def __init__(self) -> None:
        self._future_id = 0
        self._futures: dict[int, asyncio.Future] = {}

    def register(self) -> int:
        self._future_id = (self._future_id + 1) % sys.maxsize
        self._futures[self._future_id] = asyncio.get_event_loop().create_future()
        return self._future_id

    def set(self, echo: int, data: dict[str, Any]) -> None:
        if future := self._futures.get(echo):
            future.set_result(data)

    async def get(self, future_id: int, timeout: float) -> dict[str, Any]:
        if not (future := self._futures.get(future_id)):
            raise KeyError(f'future id {future_id} does not exist')
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            del self._futures[future_id]
