import json
from django.urls import reverse
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from .models import Chat, Message, Order, Notification

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.group_name = f"chat_{self.chat_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @database_sync_to_async
    def get_system_user(self):
        return User.objects.get(username='system')

    @database_sync_to_async
    def get_chat_order_pk(self, chat_id):
        chat = Chat.objects.get(pk=chat_id)
        return chat.order.pk

    @database_sync_to_async
    def get_cancel_reason(self, chat, typ):
        last_request_msg = Message.objects.filter(
            chat=chat,
            is_system=True,
            extra_data__type=f"{typ}_request",
            extra_data__response__isnull=True
        ).last()
        return last_request_msg.extra_data.get('reason', '') if last_request_msg else ''
    
    @database_sync_to_async
    def get_order_title(self, order_pk):
        return Order.objects.get(pk=order_pk).title

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        user = self.scope['user']
        chat = await database_sync_to_async(Chat.objects.get)(pk=self.chat_id)
        system_user = await self.get_system_user()

        if action == 'cancel_request':
            reason = data.get('reason', '')
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=system_user,
                text=f"Заказчик запросил отмену: «{reason}». Согласны?",
                is_system=True,
                extra_data={'type': 'cancel_request', 'reason': reason}
            )
            await self._send_system_message(msg)
            return

        if action == 'complete_request':
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=system_user,
                text="Заказчик считает заказ выполненным. Подтверждаете?",
                is_system=True,
                extra_data={'type': 'complete_request'}
            )
            await self._send_system_message(msg)
            return

        if action in ('cancel_response', 'complete_response'):
            resp = data.get('response')
            typ = 'cancel' if 'cancel' in action else 'complete'
            text = ("Фрилансер согласен" if resp == 'yes' else "Фрилансер не согласен") + (
                " с отменой заказа." if typ == 'cancel' else " с завершением заказа."
            )

            last_req_qs = Message.objects.filter(
                chat=chat,
                is_system=True,
                extra_data__type=f"{typ}_request",
                extra_data__response__isnull=True
            )
            last_req = await database_sync_to_async(lambda: last_req_qs.last())()
            if last_req:
                extra = last_req.extra_data or {}
                extra['response'] = resp
                last_req.extra_data = extra
                await database_sync_to_async(last_req.save)()

            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=system_user,
                text=text,
                is_system=True,
                extra_data={'type': action, 'response': resp}
            )
            await self._send_system_message(msg)

            if resp == 'yes':
                order_pk = await self.get_chat_order_pk(self.chat_id)
                if typ == 'cancel':
                    reason = await self.get_cancel_reason(chat, typ)
                    await self._mark_order_cancelled(order_pk, reason)
                else:
                    await self._mark_order_completed(order_pk)
                await self._deactivate_chat(self.chat_id)
            return

        if action == 'message':
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=user,
                text=data.get('message', ''),
                is_system=False
            )
            await self._send_user_message(msg, user)

            other_id = chat.client_id if user.id == chat.freelancer_id else chat.freelancer_id
            other = await database_sync_to_async(User.objects.get)(pk=other_id)

            order_title = await self.get_order_title(chat.order_id)

            note = await database_sync_to_async(Notification.objects.create)(
                user=other,
                verb=f'Новое сообщение в чате по заказу «{order_title}»',
                link=reverse('chat_detail', args=[chat.pk])
            )
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f'notifications_{other.id}',
                {
                    'type': 'notif_message',
                    'data': {
                        'id': note.id,
                        'verb': note.verb,
                        'link': note.get_absolute_url(),
                        'created_at': note.created_at.strftime('%d.%m.%Y %H:%M'),
                    }
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def _send_system_message(self, msg):
        payload = {
            'type': 'chat.message',
            'message': msg.text,
            'sender': 'system',
            'sender_id': msg.sender.id if msg.sender else None,
            'avatar_url': msg.sender.avatar.url if msg.sender and msg.sender.avatar else '',
            'sender_full_name': msg.sender.full_name or msg.sender.username if msg.sender else 'Система',
            'time': msg.timestamp.strftime('%H:%M'),
            'date': msg.timestamp.strftime('%Y-%m-%d'),
            'date_readable': msg.timestamp.strftime('%d.%m.%Y'),
            'is_system': True,
            'extra_data': msg.extra_data,
            'message_type': msg.extra_data.get('type', '') if msg.extra_data else '',
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
            'message_type': 'user_message',
        }
        await self.channel_layer.group_send(self.group_name, payload)

    @database_sync_to_async
    def _mark_order_cancelled(self, order_pk, reason):
        order = Order.objects.get(pk=order_pk)
        order.status = 'Cancelled'
        order.reason_of_cancel = reason
        order.save()

    @database_sync_to_async
    def _mark_order_completed(self, order_pk):
        order = Order.objects.get(pk=order_pk)
        order.status = 'Completed'
        order.save()

    @database_sync_to_async
    def _deactivate_chat(self, chat_id):
        chat = Chat.objects.get(pk=chat_id)
        chat.is_active = False
        chat.save()


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            return await self.close()
        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notif_message(self, event):
        await self.send_json(event["data"])
