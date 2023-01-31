import re
import ujson
import base64
from typing import Any, Iterable
from pathlib import Path
from functools import reduce
from dataclasses import dataclass


@dataclass()
class MessageSegment:
    type: str
    data: dict[str, Any]

    def to_json_obj(self) -> Any:
        return {'type': self.type, 'data': self.data}


class Message:
    def __init__(self, *segments: MessageSegment):
        self._segments = segments

    @property
    def segments(self) -> tuple[MessageSegment, ...]:
        return self._segments

    @property
    def plain_text(self) -> str:
        return ''.join(seg.data['text'] for seg in self._segments if seg.type == 'text')

    def to_json_obj(self) -> Any:
        if len(self._segments) == 1:
            return self._segments[0].to_json_obj()
        return [seg.to_json_obj() for seg in self._segments]


def _unescape(content: str) -> str:
    fragments = {
        '&amp;': '&',
        '&#91': '[',
        '&#93': ']',
        '&#44': ',',
    }
    return reduce(lambda a, b: a.replace(*b), fragments.items(), content)


def _file_to_uri(file: bytes | Path | str) -> str:
    if isinstance(file, Path):
        return file.resolve().as_uri()

    if isinstance(file, bytes):
        return 'base64://' + base64.b64encode(file).decode()

    return file


def text(content: str) -> MessageSegment:
    return MessageSegment(type='text', data={'text': content})


def at(qq: int, name: str = '') -> MessageSegment:
    return MessageSegment(type='at', data={'qq': qq, 'name': name})


def image(file: bytes | Path | str, cache: bool = True) -> MessageSegment:
    return MessageSegment(type='image', data={'file': _file_to_uri(file), 'cache': cache})


def record(file: bytes | Path | str, cache: bool = True) -> MessageSegment:
    return MessageSegment(type='record', data={'file': _file_to_uri(file), 'cache': cache})


def poke(qq: str) -> MessageSegment:
    return MessageSegment(type='poke', data={'qq': qq})


def xml(data: str) -> MessageSegment:
    return MessageSegment(type='xml', data={'data': data})


def json(data: dict[str, Any]) -> MessageSegment:
    return MessageSegment(type='json', data={'data': ujson.dumps(data)})


def parse_cq_message(msg: str) -> Message:
    def iter_message() -> Iterable[tuple[str, str]]:
        text_begin = 0
        for code in re.finditer(
            r'\[CQ:(?P<type>[a-zA-Z0-9-_.]+)'
            r'(?P<params>'
            r'(?:,[a-zA-Z0-9-_.]+=[^,\]]*)*'
            r'),?]',
            msg,
        ):
            yield 'text', msg[text_begin: code.pos + code.start()]
            text_begin = code.pos + code.end()
            yield code.group('type'), code.group('params').lstrip(',')
        yield 'text', msg[text_begin:]

    def iter_segments() -> Iterable[MessageSegment]:
        for typ, data in iter_message():
            if typ == 'text':
                if data:
                    yield text(_unescape(data))
                continue

            segment_data = {
                k: _unescape(v)
                for k, v in (x.lstrip().split('=', maxsplit=1) for x in data.split(','))
            } if data else {}

            if typ == 'at':
                yield at(int(segment_data['qq']), segment_data.get('name', ''))
                continue

            yield MessageSegment(typ, segment_data)

    return Message(*iter_segments())
