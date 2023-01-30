from shirasu import Client, Addon, MessageEvent, command


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Echo what you send.',
)


@echo.receive(command('echo'))
async def receive_echo(client: Client, event: MessageEvent) -> None:
    await client.send(event.arg)
