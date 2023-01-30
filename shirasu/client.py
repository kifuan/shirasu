import ujson
import asyncio

from typing import Any
from pathlib import Path
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import connect, WebSocketClientProtocol

from .di import di
from .addon import AddonPool
from .config import load_config, GlobalConfig
from .logger import logger
from .util import FutureTable, retry
from .event import Event, MessageEvent, NoticeEvent, RequestEvent


class ActionFailedError(Exception):
    def __init__(self, data: dict[str, Any]):
        self.msg: str = data.get('msg', '')
        self.wording: str = data.get('wording', '')
        super().__init__(self.msg)


class Client:
    """
    The websocket client.
    """

    def __init__(self, ws: WebSocketClientProtocol, global_config: GlobalConfig):
        self._ws = ws
        self._futures = FutureTable()
        self._tasks: set[asyncio.Task] = set()
        self._event: Event | None = None
        self._global_config = global_config
        di.provide('global_config', self._provide_global_config, check_duplicate=False)
        di.provide('event', self._provide_event, check_duplicate=False)
        di.provide('client', self._provide_client, check_duplicate=False)

    async def _provide_global_config(self) -> GlobalConfig:
        return self._global_config

    async def _provide_event(self) -> Event:
        return self._event

    async def _provide_client(self) -> 'Client':
        return self

    async def _handle(self, data: dict[str, Any]) -> None:
        if echo := data.get('echo'):
            self._futures.set(int(echo), data)
            return

        post_type = data.get('post_type')
        if post_type == 'meta_event':
            return

        logger.info(f'Received event {data}')

        self._event = None
        if post_type == 'message':
            self._event = MessageEvent(data)
        elif post_type == 'request':
            self._event = RequestEvent(data)
        elif post_type == 'notice':
            self._event = NoticeEvent(data)
        else:
            logger.warning(f'Ignoring unknown event {post_type}.')
            return

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
    async def listen(cls, config: str | Path = 'shirasu.json') -> None:
        """
        Start listening the websocket url.
        :param config: the path to config file.
        """

        conf = load_config(config)
        async with connect(conf.ws) as ws:
            logger.success('Connected to websocket.')
            await cls(ws, conf)._do_listen()

    async def call_action(self, action: str, **params: Any) -> dict[str, Any]:
        """
        Calls action via websocket.
        :param action: the action.
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

        data = await self._futures.get(future_id, self._global_config.action_timeout)
        if data.get('status') == 'failed':
            raise ActionFailedError(data)

        return data.get('data', {})
