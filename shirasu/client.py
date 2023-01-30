import ujson
import asyncio

from typing import Any
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import connect, WebSocketClientProtocol

from .di import di
from .logger import logger
from .context import Context
from .internal import FutureTable, retry


class Client:
    def __init__(self, ws: WebSocketClientProtocol):
        self._ws = ws
        self._futures = FutureTable()
        self._tasks: set[asyncio.Task] = set()
        self._data = {}
        di.provide(self._provide_context, check_duplicate=False)

    async def _provide_context(self) -> Context:
        return Context(self, self._data)

    async def handle(self, data: dict[str, Any]) -> None:
        self._data = data

        if data['post_type'] == 'meta_event':
            return

    async def call_action(self, action: str, timeout: float = 30., **params: Any) -> dict[str, Any]:
        future_id = self._futures.register()
        await self._ws.send(ujson.dumps({
            'action': action,
            'params': params,
            'echo': future_id,
        }))
        return await self._futures.get(future_id, timeout)

    async def do_listen(self) -> None:
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

    @classmethod
    @retry(timeout=5., messages={
        ConnectionClosedError: 'Connection closed',
        ConnectionRefusedError: 'Connection refused',
    })
    async def listen(cls, url: str) -> None:
        async with connect(url) as ws:
            client = cls(ws)
            await client.do_listen()
