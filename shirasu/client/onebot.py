import ujson
import asyncio

from pathlib import Path
from typing import Any, Literal
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import connect, WebSocketClientProtocol

from .client import Client, ClientActionError
from ..addon import AddonPool
from ..config import load_config, GlobalConfig
from ..logger import logger
from ..util import FutureTable, retry
from ..event import MessageEvent, NoticeEvent, RequestEvent
from ..message import Message


class OneBotClient(Client):
    def __init__(self, ws: WebSocketClientProtocol, pool: AddonPool, global_config: GlobalConfig):
        super().__init__(pool, global_config)
        self._ws = ws
        self._futures = FutureTable()
        self._tasks: set[asyncio.Task] = set()

    async def _call_action(self, action: str, **params: Any) -> dict[str, Any]:
        """
        Calls action via websocket.
        :param action: the action.
        :param params: the params to call the action.
        :return: the action result.
        """

        logger.info(f'Calling action {action}.')
        future_id = self._futures.register()
        await self._ws.send(ujson.dumps({
            'action': action,
            'params': params,
            'echo': future_id,
        }))

        data = await self._futures.get(future_id, self._global_config.action_timeout)
        if data.get('status') == 'failed':
            raise ClientActionError(data)

        return data.get('data', {})

    async def _handle(self, data: dict[str, Any]) -> None:
        if echo := data.get('echo'):
            self._futures.set(int(echo), data)
            return

        post_type = data.get('post_type')
        if post_type == 'meta_event':
            return

        logger.info(f'Received event {data}')

        self.curr_event = None
        if post_type == 'message':
            self.curr_event = MessageEvent.from_data(data)
        elif post_type == 'request':
            self.curr_event = RequestEvent.from_data(data)
        elif post_type == 'notice':
            self.curr_event = NoticeEvent.from_data(data)
        else:
            logger.warning(f'Ignoring unknown event {post_type}.')
            return

        await self.apply_addons()

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
    async def listen(cls, *, pool: AddonPool, config: str | Path = 'shirasu.yml') -> None:
        """
        Start listening the websocket url.
        :param pool: the addon pool, which can be used to preload plugins.
        :param config: the path to config file.
        """

        conf = load_config(config)
        async with connect(conf.ws) as ws:
            logger.success('Connected to websocket.')
            await cls(ws, pool, conf)._do_listen()

    async def send_msg(
            self,
            *,
            message_type: Literal['private', 'group'],
            user_id: int,
            group_id: int | None,
            message: Message,
            is_rejected: bool,
    ) -> int:
        res = await self._call_action(
            action='send_msg',
            message=message.to_json_obj(),
            user_id=user_id,
            group_id=group_id,
            message_type=message_type,
            is_rejected=is_rejected,
        )
        return res['message_id']
