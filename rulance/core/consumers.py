from channels.generic.websocket import AsyncWebsocketConsumer
import json

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
        message = data["message"]
        sender = self.scope["user"].username
        # Сохраняем в БД
        from .models import Message, Chat
        chat = await database_sync_to_async(Chat.objects.get)(pk=self.chat_id)
        msg = Message(chat=chat, sender=self.scope["user"], text=message)
        await database_sync_to_async(msg.save)()

        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "message": message, "sender": sender}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"]
        }))