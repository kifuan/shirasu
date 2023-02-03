import pytest
import asyncio
from shirasu import MockClient, AddonPool, at
from shirasu.config import GlobalConfig
from shirasu.event import MOCK_SELF_ID, MOCK_USER_ID
from shirasu.addon import (
    DuplicateAddonError,
    LoadAddonError,
)


def test_pool_load_error():
    pool = AddonPool()
    pool.load_module('shirasu.addons.echo')

    with pytest.raises(DuplicateAddonError):
        pool.load_module('shirasu.addons.echo')

    with pytest.raises(LoadAddonError):
        pool.load_module('@dummy_module')


@pytest.mark.asyncio
async def test_echo():
    pool = AddonPool.from_modules('shirasu.addons.echo')
    client = MockClient(pool)

    await client.post_message('/echo hello')
    echo_msg = await client.get_message()
    assert echo_msg.plain_text == 'hello'

    await client.post_message('echo hello')
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()


@pytest.mark.asyncio
async def test_square():
    pool = AddonPool.from_modules('shirasu.addons.square')
    client = MockClient(pool)

    await client.post_message('/square 2')
    square2_msg = await client.get_message()
    assert square2_msg.plain_text == '4'

    await client.post_message('/square a')
    rejected_msg = await client.get_message_event()
    assert rejected_msg.is_rejected


@pytest.mark.asyncio
async def test_tome():
    pool = AddonPool.from_modules('shirasu.addons.reject_tome')
    client = MockClient(pool)

    await client.post_message(at(MOCK_SELF_ID), message_type='group')
    rejected_msg = await client.get_message_event()
    assert rejected_msg.is_rejected

    await client.post_message('hello')
    rejected_private_msg = await client.get_message_event()
    assert rejected_private_msg.is_rejected

    await client.post_message('hello', message_type='group')
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()


@pytest.mark.asyncio
async def test_superuser_manage_disable():
    pool = AddonPool.from_modules(
        'shirasu.addons.echo',
        'shirasu.addons.manage',
    )
    config = GlobalConfig()
    client = MockClient(pool, config)

    await client.post_message('/manage disable echo')
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()

    # Disable the echo
    config.superusers = [MOCK_USER_ID]
    await client.post_message('/manage disable echo')
    disabled_msg = await client.get_message_event()
    assert not disabled_msg.is_rejected

    # Disabled echo should not work properly.
    await client.post_message('/echo foo')
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()


@pytest.mark.asyncio
async def test_manage():
    pool = AddonPool.from_modules(
        'shirasu.addons.echo',
        'shirasu.addons.manage',
    )
    config = GlobalConfig(superusers=[MOCK_USER_ID])
    client = MockClient(pool, config)

    for invalid_command in ('/manage', '/manage ace', '/manage ace taffy', '/manage disable taffy'):
        await client.post_message(invalid_command)
        rejected_msg = await client.get_message_event()
        assert rejected_msg.is_rejected

    await client.post_message('/manage disable echo')
    disabled_msg = await client.get_message_event()
    assert not disabled_msg.is_rejected

    await client.post_message('/echo foo')
    with pytest.raises(asyncio.TimeoutError):
        await client.get_message()

    await client.post_message('/manage enable echo')
    enabled_msg = await client.get_message_event()
    assert not enabled_msg.is_rejected

    await client.post_message('/echo foo')
    foo_msg = await client.get_message()
    assert foo_msg.plain_text == 'foo'
