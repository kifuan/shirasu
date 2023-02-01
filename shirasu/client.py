import ujson
import asyncio

from pathlib import Path
from itertools import compress
from typing import Any, Literal
from asyncio.queues import Queue
from abc import ABC, abstractmethod
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.client import connect, WebSocketClientProtocol

from .di import di
from .addon import AddonPool
from .config import load_config, GlobalConfig
from .logger import logger
from .util import FutureTable, retry
from .event import Event, MessageEvent, NoticeEvent, RequestEvent, mock_message_event
from .message import Message, MessageSegment, text


class ActionFailedError(Exception):
    def __init__(self, data: dict[str, Any]):
        self.msg: str = data.get('msg', '')
        self.wording: str = data.get('wording', '')
        super().__init__(self.msg)


class Client(ABC):
    """
    The client to send and receive messages.
    """

    def __init__(self, pool: AddonPool, global_config: GlobalConfig):
        self.curr_event: Event | None = None
        self._pool = pool
        self._global_config = global_config
        di.provide('client', lambda: self, sync=True, check_duplicate=False)
        di.provide('pool', lambda: self._pool, sync=True, check_duplicate=False)
        di.provide('event', lambda: self.curr_event, sync=True, check_duplicate=False)
        di.provide('global_config', lambda: self._global_config, sync=True, check_duplicate=False)

    @abstractmethod
    async def send_msg(
            self,
            *,
            message_type: Literal['private', 'group'],
            user_id: int,
            group_id: int | None,
            message: Message
    ) -> int:
        raise NotImplementedError()

    async def send(self, message: Message | str | MessageSegment) -> int:
        if not isinstance(self.curr_event, MessageEvent):
            logger.warning('Attempted to send message back when current event is not message event.')
            return -1

        if isinstance(message, str):
            message = text(message)
        if isinstance(message, MessageSegment):
            message = Message(message)

        return await self.send_msg(
            message=message,
            user_id=self.curr_event.user_id,
            group_id=self.curr_event.group_id,
            message_type=self.curr_event.message_type,
        )

    async def apply_addons(self) -> None:
        """
        Applies all addons.
        """

        selectors = await asyncio.gather(*(addon.do_match() for addon in self._pool))
        matched_addons = list(compress(self._pool, selectors))

        if not (count := len(matched_addons)):
            return

        addon = matched_addons[0]
        if count > 1:
            logger.warning(f'Matched {count} conflict addons, only applies the first: {addon.name}.')

        await addon.do_receive()


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
    async def listen(cls, *, pool: AddonPool, config: str | Path = 'shirasu.json') -> None:
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
            message: Message
    ) -> int:
        res = await self._call_action(
            action='send_msg',
            message=message.to_json_obj(),
            user_id=user_id,
            group_id=group_id,
            message_type=message_type,
        )
        return res['message_id']


class MockClient(Client):
    def __init__(self, pool: AddonPool, global_config: GlobalConfig | None = None):
        super().__init__(pool, global_config or GlobalConfig())
        self._message_queue: Queue[MessageEvent] = Queue()

    async def post_event(self, event: Event) -> None:
        self.curr_event = event
        await self.apply_addons()

    async def send_msg(
            self,
            *,
            message_type: Literal['private', 'group'],
            user_id: int,
            group_id: int | None,
            message: Message
    ) -> int:
        await self._message_queue.put(mock_message_event(
            message_type=message_type,
            message=message,
            group_id=group_id,
            user_id=user_id,
        ))
        return -1

    async def get_message(self, timeout: float = .1):
        return await asyncio.wait_for(self._message_queue.get(), timeout)
