from shirasu import Addon, Client, tome


addon = Addon(
    name='reject_tome',
    usage='At the bot or send private messages to the bot.',
    description='Rejects if current event is to the bot.'
)


@addon.receive(tome())
async def receive_tome(client: Client) -> None:
    await client.reject('Do not send message to me!')
