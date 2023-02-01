from shirasu import Client, Addon, MessageEvent, command


echo = Addon(
    name='square',
    usage='/square number',
    description='Calculates the square of given number.',
)


@echo.receive(command('square'))
async def receive_square(client: Client, event: MessageEvent) -> None:
    arg = event.arg

    try:
        num = float(arg)
        await client.send(f'{pow(num, 2):g}')
    except ValueError:
        await client.reject(f'Invalid number: {arg}')
