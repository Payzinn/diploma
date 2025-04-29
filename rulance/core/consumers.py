from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from .models import Chat, Message

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
        text = data["message"]
        user = self.scope["user"]

        chat = await database_sync_to_async(Chat.objects.get)(pk=self.chat_id)
        msg  = await database_sync_to_async(Message.objects.create)(
            chat=chat, sender=user, text=text
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": text,
                "sender": user.username,
                "sender_id": user.id,
                "avatar_url": user.avatar.url or "",
                "sender_full_name": user.full_name or user.username,
                "time": msg.timestamp.strftime("%H:%M"),
                "date": msg.timestamp.strftime("%Y-%m-%d"),
                "date_readable": msg.timestamp.strftime("%d.%m.%Y"),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
