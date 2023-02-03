from shirasu import Addon, AddonPool, Client, MessageEvent, superuser, command


manage = Addon(
    name='manage',
    usage='/manage disable|enable name',
    description='Manage your addons, including itself.',
)


@manage.receive(superuser() & command('manage'))
async def handle_manage(client: Client, pool: AddonPool, event: MessageEvent) -> None:
    if len(event.args) != 2:
        await client.reject(f'Invalid arguments count: {len(event.args)}, expected 2.')
        return

    mode, name = event.args
    if not pool.has_addon(name):
        await client.reject(f'Addon {name} does not exist.')
        return

    if mode == 'disable':
        pool.set_addon_disabled(name, disabled=True)
        await client.send(f'Disabled addon {name} successfully.')
    elif mode == 'enable':
        pool.set_addon_disabled(name, disabled=False)
        await client.send(f'Enabled addon {name} successfully.')
    else:
        await client.reject(f'Unknown mode: {mode}, expected disable or enable.')
