from typing import Any, Literal, TYPE_CHECKING
from .message import Message, MessageSegment, text, parse_cq_message
from .logger import logger

if TYPE_CHECKING:
    from .client import Client


COMMAND_START = ['/']


class Context:
    def __init__(self, client: "Client", data: dict[str, Any]) -> None:
        self._client = client
        self._data = data
        self._arg = ''

    def match_command(self, cmd: str) -> bool:
        t = self.message.plain_text
        for start in COMMAND_START:
            prefix = start + cmd
            if t.startswith(prefix):
                self._arg = t.removeprefix(prefix).strip()
                return True
        return False

    @property
    def post_type(self) -> Literal['message', 'request', 'notice', 'meta_event']:
        t = self._data.get('post_type')
        assert t, 'Must check if the event is API result before getting from context.'
        return t

    @property
    def user_id(self) -> int | None:
        return self._data.get('user_id')

    @property
    def group_id(self) -> int | None:
        return self._data.get('group_id')

    @property
    def notice(self) -> str:
        return self._data.get('notice', '')

    @property
    def message(self) -> Message:
        return parse_cq_message(self._data.get('raw_message', ''))

    @property
    def arg(self) -> str:
        return self._arg

    async def send_private_msg(self, user_id: int, message: Message) -> int:
        msg = await self._client.call_action(
            action='send_private_msg',
            user_id=user_id,
            message=message.to_json_obj(),
        )
        return msg['message_id']

    async def send_group_msg(self, group_id: int, message: Message) -> int:
        msg = await self._client.call_action(
            action='send_group_msg',
            group_id=group_id,
            message=message.to_json_obj(),
        )
        return msg['message_id']

    async def send(self, message: Message | MessageSegment | str) -> int:
        if isinstance(message, str):
            message = text(message)
        if isinstance(message, MessageSegment):
            message = Message(message)

        if group_id := self.group_id:
            return await self.send_group_msg(group_id, message)
        elif user_id := self.user_id:
            return await self.send_private_msg(user_id, message)

        logger.warning('Attempted to send message without group id or user id in the context.')
        return -1
