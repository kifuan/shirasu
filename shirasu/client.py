import ujson
import asyncio

from typing import Any
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import connect, WebSocketClientProtocol

from .di import di
from .addon import AddonPool
from .logger import logger
from .context import Context
from .util import FutureTable, retry


class ActionFailedError(Exception):
    def __init__(self, data: dict[str, Any]):
        self.msg: str = data.get('msg', '')
        self.wording: str = data.get('wording', '')
        super().__init__(self.msg)


class Client:
    """
    The websocket client.
    """

    def __init__(self, ws: WebSocketClientProtocol):
        self._ws = ws
        self._futures = FutureTable()
        self._tasks: set[asyncio.Task] = set()
        self._ctx: Context | None = None
        di.provide('ctx', self._provide_context, check_duplicate=False)

    async def _provide_context(self) -> Context:
        assert self._ctx is not None
        return self._ctx

    async def _handle(self, data: dict[str, Any]) -> None:
        self._ctx = Context(self, data)

        if echo := data.get('echo'):
            self._futures.set(int(echo), data)
            return

        post_type = data.get('post_type')
        if post_type == 'meta_event':
            return

        if message := data.get('message'):
            logger.info(f'Received message {message}')

        await asyncio.gather(*(p.do_receive() for p in AddonPool()))

    async def _do_listen(self) -> None:
        if count := len(self._tasks):
            logger.warning(f'Canceling {count} undone tasks')
            for task in self._tasks:
                task.cancel()
            self._tasks.clear()

        async for message in self._ws:
            if isinstance(message, bytes):
                message = message.decode('utf8')
            task = asyncio.create_task(self._handle(ujson.loads(message)))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

    @classmethod
    @retry(timeout=5., messages={
        ConnectionClosedError: 'Connection closed',
        ConnectionRefusedError: 'Connection refused',
    })
    async def listen(cls, url: str) -> None:
        """
        Start listening the websocket url.
        :param url: the url to listen.
        """

        async with connect(url) as ws:
            logger.success('Connected to websocket.')
            await cls(ws)._do_listen()

    async def call_action(self, action: str, timeout: float = 30., **params: Any) -> dict[str, Any]:
        """
        Calls action via websocket.
        :param action: the action.
        :param timeout: the timeout.
        :param params: the params to call the action.
        :return: the action result.
        """

        logger.info(f'Calling {action} with {params}')
        future_id = self._futures.register()
        await self._ws.send(ujson.dumps({
            'action': action,
            'params': params,
            'echo': future_id,
        }))

        data = await self._futures.get(future_id, timeout)
        if data.get('status') == 'failed':
            raise ActionFailedError(data)

        return data.get('data', {})
