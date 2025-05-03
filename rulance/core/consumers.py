import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Chat, Message, Order

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.group_name = f"chat_{self.chat_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"Добавлен {self.channel_name} в группу {self.group_name}")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"Удалён {self.channel_name} из группы {self.group_name}")

    @database_sync_to_async
    def get_system_user(self):
        return User.objects.get(username='system')

    @database_sync_to_async
    def get_chat_order_pk(self, chat_id):
        chat = Chat.objects.get(pk=chat_id)
        if not chat.order:
            raise ValueError("Chat has no associated order")
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

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            user = self.scope['user']
            chat = await database_sync_to_async(Chat.objects.get)(pk=self.chat_id)
            system_user = await self.get_system_user()

            if action == 'cancel_request':
                reason = data.get('reason', '')
                system_msg = await database_sync_to_async(Message.objects.create)(
                    chat=chat,
                    sender=system_user,
                    text=f"Заказчик запросил отмену: «{reason}». Согласны?",
                    is_system=True,
                    extra_data={'type': 'cancel_request', 'reason': reason}
                )
                await self._send_system_message(system_msg)
                return

            if action == 'complete_request':
                system_msg = await database_sync_to_async(Message.objects.create)(
                    chat=chat,
                    sender=system_user,
                    text="Заказчик считает заказ выполненным. Подтверждаете?",
                    is_system=True,
                    extra_data={'type': 'complete_request'}
                )
                await self._send_system_message(system_msg)
                return

            if action in ('cancel_response', 'complete_response'):
                resp = data.get('response')
                typ = 'cancel' if 'cancel' in action else 'complete'
                text = (
                    "Фрилансер согласен" if resp == 'yes' else "Фрилансер не согласен"
                ) + (" с отменой заказа." if typ == 'cancel' else " с завершением заказа.")

                last_request_msg = await database_sync_to_async(Message.objects.filter)(
                    chat=chat,
                    is_system=True,
                    extra_data__type=f"{typ}_request",
                    extra_data__response__isnull=True
                )
                last_request_msg = await database_sync_to_async(last_request_msg.last)()

                if last_request_msg:
                    extra_data = last_request_msg.extra_data or {}
                    extra_data['response'] = resp
                    last_request_msg.extra_data = extra_data
                    await database_sync_to_async(last_request_msg.save)()
                    print(f"Обновлено сообщение {last_request_msg.id} с ответом: {resp}")

                system_msg = await database_sync_to_async(Message.objects.create)(
                    chat=chat,
                    sender=system_user,
                    text=text,
                    is_system=True,
                    extra_data={'type': action, 'response': resp}
                )
                await self._send_system_message(system_msg)

                if resp == 'yes':
                    try:
                        order_pk = await self.get_chat_order_pk(self.chat_id)
                        if typ == 'cancel':
                            cancel_reason = await self.get_cancel_reason(chat, typ)
                            await self._mark_order_cancelled(order_pk, cancel_reason)
                        else:
                            await self._mark_order_completed(order_pk)
                        await self._deactivate_chat(self.chat_id)
                        print(f"Чат {self.chat_id} деактивирован, заказ {order_pk} обновлён")
                    except Exception as e:
                        print(f"Ошибка при изменении статуса заказа или чата: {e}")
                return

            text = data.get('message', '')
            is_chat_active = await database_sync_to_async(lambda: Chat.objects.get(pk=self.chat_id).is_active)()
            if not is_chat_active:
                print(f"Попытка отправить сообщение в неактивный чат {self.chat_id}")
                return
            msg = await database_sync_to_async(Message.objects.create)(
                chat=chat,
                sender=user,
                text=text,
                is_system=False
            )
            await self._send_user_message(msg, user)

        except Exception as e:
            print(f"Ошибка в методе receive: {e}")

    async def chat_message(self, event):
        print(f"Обработка события chat_message: {event}")
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
        print(f"Отправка системного сообщения в группу {self.group_name}: {payload}")
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
        print(f"Отправка пользовательского сообщения в группу {self.group_name}: {payload}")
        await self.channel_layer.group_send(self.group_name, payload)

    @database_sync_to_async
    def _mark_order_cancelled(self, order_pk, reason):
        order = Order.objects.get(pk=order_pk)
        print(f"Обновление заказа {order_pk}: статус=Canceled, причина={reason}")
        order.status = 'Cancelled'
        order.reason_of_cancel = reason
        order.save()
        print(f"Заказ {order_pk} обновлён: статус={order.status}, reason_of_cancel={order.reason_of_cancel}")

    @database_sync_to_async
    def _mark_order_completed(self, order_pk):
        order = Order.objects.get(pk=order_pk)
        print(f"Обновление заказа {order_pk}: статус=Completed")
        order.status = 'Completed'
        order.save()
        print(f"Заказ {order_pk} обновлён: статус={order.status}")

    @database_sync_to_async
    def _deactivate_chat(self, chat_id):
        chat = Chat.objects.get(pk=chat_id)
        chat.is_active = False
        chat.save()
        print(f"Чат {chat_id} деактивирован")