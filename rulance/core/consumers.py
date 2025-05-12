import json
from django.urls import reverse
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone
import pytz
from .models import *
from .models import Chat, Message, Order, Notification
from .utils import update_profile_tab  

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
    def get_chat(self):
        # Grab client, freelancer and order in one go
        return Chat.objects.select_related('client','freelancer','order') \
                           .get(pk=self.chat_id)

    @database_sync_to_async
    def get_cancel_reason(self, chat, typ):
        last = Message.objects.filter(
            chat=chat,
            is_system=True,
            extra_data__type=f"{typ}_request",
            extra_data__response__isnull=True
        ).last()
        return last.extra_data.get('reason','') if last else ''

    @database_sync_to_async
    def _mark_order_cancelled(self, order_pk, reason):
        o = Order.objects.get(pk=order_pk)
        o.status = 'Cancelled'
        o.reason_of_cancel = reason
        o.save()

    @database_sync_to_async
    def _mark_order_completed(self, order_pk):
        o = Order.objects.get(pk=order_pk)
        o.status = 'Completed'
        o.save()

    @database_sync_to_async
    def _deactivate_chat(self, chat_id):
        c = Chat.objects.get(pk=chat_id)
        c.is_active = False
        c.save()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        me     = self.scope['user']

        # pull chat in a single sync call
        chat   = await self.get_chat()
        system = await self.get_system_user()

        # 1) user message
        if action == 'message':
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat, sender=me, text=data.get('message',''), is_system=False
            )
            await self._send_user_message(msg, me)

            # notify the other participant
            other = chat.freelancer if me == chat.client else chat.client
            # chat.order is already fetched, no DB hit
            verb = f'Новое сообщение в чате по заказу «{chat.order.title}»'
            link = reverse('chat_detail', args=[chat.pk])
            note = await database_sync_to_async(Notification.objects.create)(
                user=other, verb=verb, link=link
            )
            await self.channel_layer.group_send(
                f'notifications_{other.id}',
                {
                    'type': 'notif_message',
                    'data': {
                        'id': note.id,
                        'verb': note.verb,
                        'link': note.get_absolute_url(),
                        'created_at': note.created_at.astimezone(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M'),
                    }
                }
            )
            return

        # 2) cancel request
        if action == 'cancel_request' and me == chat.client:
            reason = data.get('reason','')
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat, sender=system,
                text=f"Заказчик запросил отмену: «{reason}». Согласны?",
                is_system=True,
                extra_data={'type':'cancel_request','reason':reason}
            )
            await self._send_system_message(msg)
            return

        # 3) complete request
        if action == 'complete_request' and me == chat.client:
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat, sender=system,
                text="Заказчик считает заказ выполненным. Подтверждаете?",
                is_system=True,
                extra_data={'type':'complete_request'}
            )
            await self._send_system_message(msg)
            return

        # 4) freelancer response
        if action in ('cancel_response','complete_response'):
            resp = data.get('response')
            typ  = 'cancel' if 'cancel' in action else 'complete'
            text = ("Фрилансер согласен" if resp=='yes' else "Фрилансер не согласен") + (
                " с отменой заказа." if typ=='cancel' else " с завершением заказа."
            )
            # update last request
            last_req = await database_sync_to_async(lambda: Message.objects.filter(
                chat=chat,
                is_system=True,
                extra_data__type=f"{typ}_request",
                extra_data__response__isnull=True
            ).last())()
            if last_req:
                ed = last_req.extra_data or {}
                ed['response'] = resp
                last_req.extra_data = ed
                await database_sync_to_async(last_req.save)()

            # send the confirmation
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat, sender=system, text=text,
                is_system=True, extra_data={'type':action,'response':resp}
            )
            await self._send_system_message(msg)

            if resp == 'yes':
                order_pk = chat.order.pk
                if typ == 'cancel':
                    reason = await self.get_cancel_reason(chat, typ)
                    await self._mark_order_cancelled(order_pk, reason)
                else:
                    await self._mark_order_completed(order_pk)
                # deactivate chat
                await self._deactivate_chat(self.chat_id)

            return

    async def chat_message(self, event):
        # emitted by group_send(type='chat.message', …)
        await self.send(text_data=json.dumps(event))

    async def _send_system_message(self, msg):
        tz = pytz.timezone('Europe/Moscow')
        ts = msg.timestamp.astimezone(tz)
        payload = {
            'type': 'chat.message',
            'message': msg.text,
            'sender': 'system',
            'sender_id': msg.sender.id if msg.sender else None,
            'avatar_url': msg.sender.avatar.url if msg.sender and msg.sender.avatar else '',
            'sender_full_name': msg.sender.full_name or msg.sender.username if msg.sender else 'Система',
            'time': ts.strftime('%H:%M'),
            'date': ts.strftime('%Y-%m-%d'),
            'date_readable': ts.strftime('%d.%m.%Y'),
            'is_system': True,
            'extra_data': msg.extra_data,
            'message_type': msg.extra_data.get('type','') if msg.extra_data else '',
        }
        await self.channel_layer.group_send(self.group_name, payload)

    async def _send_user_message(self, msg, user):
        tz = pytz.timezone('Europe/Moscow')
        ts = msg.timestamp.astimezone(tz)
        payload = {
            'type': 'chat.message',
            'message': msg.text,
            'sender': user.username,
            'sender_id': user.id,
            'avatar_url': user.avatar.url if user.avatar else '',
            'sender_full_name': user.full_name or user.username,
            'time': ts.strftime('%H:%M'),
            'date': ts.strftime('%Y-%m-%d'),
            'date_readable': ts.strftime('%d.%m.%Y'),
            'is_system': False,
            'extra_data': {},
            'message_type': 'user_message',
        }
        await self.channel_layer.group_send(self.group_name, payload)
        
class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close()
        self.group_name = f"notifications_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notif_message(self, event):
        await self.send_json(event["data"])

class ProfileConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"profile_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def profile_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))