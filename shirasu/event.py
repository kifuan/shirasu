from typing import Any, Literal
from .message import Message, parse_cq_message


class Event:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.time: int = data['time']
        self.self_id: int = data['self_id']
        self.post_type: str = data['post_type']

    def get(self, key: str) -> Any:
        return self.data.get(key)


class MessageEvent(Event):
    post_type: Literal['message']

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.message_type: Literal['private', 'group'] = data['message_type']
        self.message: Message = parse_cq_message(data['raw_message'])
        self.user_id: int = data['user_id']
        self.group_id: int | None = data.get('group_id')
        self.arg = ''

    def match_command(self, cmd: str, command_start: list[str]) -> bool:
        t = self.message.plain_text
        for start in command_start:
            prefix = start + cmd
            if t.startswith(prefix):
                self.arg = t.removeprefix(prefix).strip()
                return True
        return False


class NoticeEvent(Event):
    post_type: Literal['notice']

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.notice_type: str = data['request_type']


class RequestEvent(Event):
    post_type: Literal['request']

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
