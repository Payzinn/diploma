from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def update_profile_tab(user, tab, count):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'profile_{user.id}',
        {'type': 'profile_updates', 'tab': tab, 'count': count}
    )