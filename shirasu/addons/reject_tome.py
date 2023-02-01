from shirasu import Addon, Client, tome


reject_tome = Addon(
    name='reject_tome',
    usage='At the bot or send private messages to the bot.',
    description='Rejects if current event is to the bot.'
)


@reject_tome.receive(tome())
async def handle_tome(client: Client) -> None:
    await client.reject('Do not send message to me!')
