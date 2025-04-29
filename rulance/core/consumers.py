import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Message, Order

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.group_name = f"chat_{self.chat_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        user = self.scope['user']
        chat = await database_sync_to_async(Chat.objects.get)(pk=self.chat_id)

        if action == 'cancel_request':
            reason = data.get('reason', '')
            system_msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=None,
                text=f"Заказчик запросил отмену: «{reason}». Согласны?",
                is_system=True,
                extra_data={'type':'cancel_request', 'reason': reason}
            )
            await self._send_system_message(system_msg)
            return

        if action == 'complete_request':
            system_msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=None,
                text="Заказчик считает заказ выполненным. Подтверждаете?",
                is_system=True,
                extra_data={'type':'complete_request'}
            )
            await self._send_system_message(system_msg)
            return

        if action in ('cancel_response', 'complete_response'):
            resp = data.get('response') 
            typ = 'cancel' if 'cancel' in action else 'complete'
            text = (
                "Фрилансер согласен" if resp=='yes' else "Фрилансер не согласен"
            ) + (" с отменой заказа." if typ=='cancel' else " с завершением заказа.")
            system_msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=None,
                text=text,
                is_system=True,
                extra_data={'type':action, 'response':resp}
            )
            await self._send_system_message(system_msg)
            if resp == 'yes':
                if typ=='cancel':
                    await self._mark_order_cancelled(chat.order.pk)
                else:
                    await self._mark_order_completed(chat.order.pk)
            return

        text = data.get('message', '')
        msg = await database_sync_to_async(Message.objects.create)(
            chat=chat,
            sender=user,
            text=text,
            is_system=False
        )
        await self._send_user_message(msg, user)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def _send_system_message(self, msg):
        payload = {
            'type': 'chat.message',
            'message': msg.text,
            'sender': 'system',
            'sender_id': None,
            'avatar_url': '',
            'sender_full_name': 'Система',
            'time': msg.timestamp.strftime('%H:%M'),
            'date': msg.timestamp.strftime('%Y-%m-%d'),
            'date_readable': msg.timestamp.strftime('%d.%m.%Y'),
            'is_system': True,
            'extra_data': msg.extra_data,
        }
        await self.channel_layer.group_send(self.group_name, payload)

    async def _send_user_message(self, msg, user):
        payload = {
            'type': 'chat.message',
            'message': msg.text,
            'sender': user.username,
            'sender_id': user.id,
            'avatar_url': user.avatar.url if user.avatar else '',
            'sender_full_name': user.full_name or user.username,
            'time': msg.timestamp.strftime('%H:%M'),
            'date': msg.timestamp.strftime('%Y-%m-%d'),
            'date_readable': msg.timestamp.strftime('%d.%m.%Y'),
            'is_system': False,
            'extra_data': {},
        }
        await self.channel_layer.group_send(self.group_name, payload)

    @database_sync_to_async
    def _mark_order_cancelled(self, order_pk):
        order = Order.objects.get(pk=order_pk)
        order.status = 'Cancelled'
        order.save()

    @database_sync_to_async
    def _mark_order_completed(self, order_pk):
        order = Order.objects.get(pk=order_pk)
        order.status = 'Completed'
        order.save()
