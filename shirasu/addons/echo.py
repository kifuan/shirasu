from shirasu import Client, Addon, MessageEvent, command


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Sends your text back.',
)


@echo.receive(command('echo'))
async def receive_echo(client: Client, event: MessageEvent) -> None:
    await client.send(event.arg)
