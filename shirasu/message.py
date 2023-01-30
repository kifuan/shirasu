import abc
from typing import Any


class Message(abc.ABC):
    @abc.abstractmethod
    def to_json_obj(self) -> Any:
        raise NotImplementedError()


class MultiMessage(Message):
    def __init__(self, *messages: Message):
        self._messages = messages

    def to_json_obj(self) -> Any:
        return self._messages


class Text(Message):
    def __init__(self, text: str) -> None:
        self._text = text

    def to_json_obj(self) -> Any:
        return {'type': 'text', 'data': {'text': self._text}}


class At(Message):
    def __init__(self, user_id: str, name: str = '') -> None:
        self._user_id = user_id
        self._name = name

    def to_json_obj(self) -> Any:
        return {'type': 'at', 'data': {'qq': self._user_id, 'name': self._name}}


class Image(Message):
    def to_json_obj(self) -> Any:
        return {''}
