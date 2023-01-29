import ujson
import asyncio
from typing import Any
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import WebSocketClientProtocol, connect
from .logger import logger
from .internal import FutureTable, retry


class Client:
    def __init__(self, ws: WebSocketClientProtocol, timeout: float):
        self._ws = ws
        self._futures = FutureTable()
        self._tasks: set[asyncio.Task] = set()
        self._timeout = timeout

    @classmethod
    @retry(timeout=5., skip=KeyboardInterrupt, messages={
        ConnectionRefusedError: 'Connection refused',
        ConnectionClosedError: 'Connection closed',
    })
    async def listen(cls, url: str, *, timeout: float = 30.) -> None:
        async with connect(url) as ws:
            client = cls(ws, timeout)
            await client.listen_no_retry()

    async def handle(self, data: dict[str, Any]):
        print(f'Received data {data}')

    async def call_action(self, action: str, **params: Any) -> dict[str, Any]:
        future_id = self._futures.register()
        await self._ws.send(ujson.dumps({
            'action': action,
            'params': params,
            'echo': future_id,
        }))
        return await self._futures.get(future_id, self._timeout)

    async def listen_no_retry(self):
        if count := len(self._tasks):
            logger.warning(f'Canceling {count} undone tasks')
            for task in self._tasks:
                task.cancel()
            self._tasks.clear()

        async for message in self._ws:
            if isinstance(message, bytes):
                message = message.decode('utf8')
            task = asyncio.create_task(self.handle(ujson.loads(message)))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
