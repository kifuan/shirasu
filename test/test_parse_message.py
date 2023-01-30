from shirasu.message import (
    parse_cq_message,
)


def test_parse_image():
    file = 'taffy.jpg'
    img = parse_cq_message(f'[CQ:image,file={file}]')
    assert img.segments[0].data['file'] == file


def test_parse_text():
    t = 'this is simple text, nothing else'
    assert parse_cq_message(t).segments[0].data['text'] == t


def test_parse_at():
    qq = 1883
    assert parse_cq_message(f'[CQ:at,qq={qq}]').segments[0].data['qq'] == qq


def test_parse_record():
    file = 'taffy.mp3'
    record = parse_cq_message(f'[CQ:record,file={file}]').segments[0]
    assert record.data['file'] == file


def test_parse_poke():
    assert parse_cq_message('[CQ:poke]').segments[0].type == 'poke'


def test_parse_xml():
    data = '<something></something>'
    xml = parse_cq_message(f'[CQ:xml,data={data}]').segments[0]
    assert xml.data['data'] == data


def test_parse_json():
    data = '{"a": true}'
    json = parse_cq_message(f'[CQ:json,data={data}]').segments[0]
    assert json.data['data'] == data
