from shirasu.message import (
    parse_cq_message,
)


def test_parse_image():
    file = 'taffy.jpg'
    msg = parse_cq_message(f'[CQ:image,file={file}]').segments[0]
    assert msg.type == 'image'
    assert msg.data['file'] == file


def test_parse_text():
    t = 'this is simple text, nothing else'
    msg = parse_cq_message(t).segments[0]
    assert msg.type == 'text'
    assert msg.data['text'] == t


def test_parse_at():
    qq = 1883
    msg = parse_cq_message(f'[CQ:at,qq={qq}]').segments[0]
    assert msg.type == 'at'
    assert msg.data['qq'] == qq


def test_parse_record():
    file = 'taffy.mp3'
    msg = parse_cq_message(f'[CQ:record,file={file}]').segments[0]
    assert msg.type == 'record'
    assert msg.data['file'] == file


def test_parse_poke():
    msg = parse_cq_message('[CQ:poke]').segments[0]
    assert msg.type == 'poke'


def test_parse_xml():
    data = '<something></something>'
    msg = parse_cq_message(f'[CQ:xml,data={data}]').segments[0]
    assert msg.type == 'xml'
    assert msg.data['data'] == data


def test_parse_json():
    data = '{"a": true}'
    msg = parse_cq_message(f'[CQ:json,data={data}]').segments[0]
    assert msg.type == 'json'
    assert msg.data['data'] == data


def test_multiple():
    segments = parse_cq_message(f'[CQ:image,file=file.jpg]text[CQ:at,qq=1883]').segments
    assert len(segments) == 3
    assert segments[0].type == 'image'
    assert segments[1].type == 'text'
    assert segments[2].type == 'at'
