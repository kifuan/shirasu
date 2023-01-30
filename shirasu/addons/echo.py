from shirasu import Client, Addon, MessageEvent, command


echo = Addon(
    name='echo',
    usage='/echo text',
    description='Echo what you send.',
)


@echo.receive(command('echo'))
async def receive_echo(client: Client, event: MessageEvent) -> None:
    await client.call_action(
        'send_msg',
        message_type=event.message_type,
        user_id=event.user_id,
        group_id=event.group_id,
        message=event.arg,
    )
