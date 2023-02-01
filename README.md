# Shirasu

## Introduction

`Shirasu` is a simple bot framework to study the principles, based on  `OneBot v11` (especially `go-cqhttp`).

出于练习英语的目的，本篇我就用简单英文写了（来自寒假末尾最后的倔强，其实是 Grammarly 监督才能避免一堆语法错误）。

## Usage

To create a simple bot application, you should create a `.py` file containing the following code:

```python
import asyncio
from shirasu import AddonPool, OneBotClient


if __name__ == '__main__':
    pool = AddonPool.from_modules(
        'shirasu.addons.echo',
        'shirasu.addons.help',
    )
    asyncio.run(OneBotClient.listen(pool=pool))
```

Then, create a `shirasu.yml`, which could be other names configured by specifying the `config` argument of `OneBotClient.listen`.

```yaml
# The WebSocket server URL(not reverse WebSocket).
ws: ws://127.0.0.1:8080

# The prefixes of commands.
command_prefixes: ['/', '']

# The configurations of addons.
addons:
  help:
    show_addon_list: true
```

For more information please see the next chapter.

## Features

There are some features slightly different from others.

### Dependency Injection System

I'm used to `Spring`'s DI system, like:

```java
@Autowired
private Foo foo;
```

I know it's better to use a setter or constructor, but let me just keep it simple.

However, DI in `FastAPI` is like this:

```python
async def get_foo() -> Foo:
    return Foo()

async def use(foo: Foo = Depends(get_foo)) -> None:
    await foo.use()
```

There are other frameworks like `Spring` for sure, but I implemented a simple DI system to study the principles.

```python
import asyncio
from datetime import datetime
from shirasu.di import inject, provide


@provide('now', sync=True)
def provide_now() -> datetime:
    return datetime.now()


@provide('today')
async def provide_today(now: datetime) -> int:
    await asyncio.sleep(.1)
    return now.day


@inject(sync=True)
def use_today(today: int) -> None:
    print(today)


@inject()
async def use_now(now: datetime) -> None:
    await asyncio.sleep(.1)
    print(now.year)


# 1
await use_today()

# 2023
await use_now()
```

Both async or sync functions will be wrapped by **async functions** eventually. The `sync` parameter is just to provide typing features provided by `@overload`.

### Addon System

Addons in `shirasu` have no business with runtime context when creating them. Therefore you can `import` them from other modules **directly** without ensuring whether they have been imported by `shirasu`.

To write an addon, take `shirasu.addons.echo` as an example:

```python
from shirasu import Client, Addon, MessageEvent, command


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Sends your text back.',
)


@echo.receive(command('echo'))
async def handle_echo(client: Client, event: MessageEvent) -> None:
    await client.send(event.arg)
```

Note that the receiver(i.e. `handle_echo`) **is injected automatically**, so you don't need to add `@inject()` decorator to it.

For configurations, take `shirasu.addons.square` as an example:

```python
from pydantic import BaseModel
from shirasu import Client, Addon, MessageEvent, command


class SquareConfig(BaseModel):
    precision: int = 2


square = Addon(
    name='square',
    usage='/square number',
    description='Calculates the square of given number.',
    config_model=SquareConfig,
)


@square.receive(command('square'))
async def handle_square(client: Client, event: MessageEvent, config: SquareConfig) -> None:
    arg = event.arg

    try:
        result = round(float(arg) ** 2, config.precision)
        await client.send(f'{result:g}')
    except ValueError:
        await client.reject(f'Invalid number: {arg}')
```

The configurations should be written in `shirasu.yml`, for example, if you want to set the `precision` to `3`:

```yaml
# Configurations for addons.
addons:
  square:
    # Configurations for addon square.
    precision: 3
```

### Unit tests

It's hard to write tests for some frameworks, so I tried my best to make it simple for this framework.

To start with, you should install `pytest` and `pytest-asyncio` as our framework is designed to be async. Take the `square` addon as an example:

```python
import pytest
import asyncio
from shirasu import MockClient, AddonPool


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
```

However, if your addon does not send any message sometimes, you could assert that the `asyncio.TimeoutError` will be raised. Take the `echo` addon as an example:

```python
import pytest
import asyncio
from shirasu import MockClient, AddonPool


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
```

In this case, we tested the `command_prefixes`, not the addon itself.