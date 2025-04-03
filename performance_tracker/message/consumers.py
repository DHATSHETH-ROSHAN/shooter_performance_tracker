import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
from users.models import UserProfiles

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles WebSocket connection"""
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        # Add the user to the WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handles incoming messages"""
        data = json.loads(text_data)
        sender_id = data["sender_id"]
        receiver_id = data["receiver_id"]
        content = data["message"]

        sender = await self.get_user(sender_id)
        receiver = await self.get_user(receiver_id)

        if sender and receiver:
            # Save message in the database
            message = await self.save_message(sender, receiver, content, self.conversation_id)

            # Send message to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "sender": sender.username,
                    "receiver": receiver.username,
                    "message": content,
                    "timestamp": str(message.timestamp),
                    "conversation_id": self.conversation_id,
                }
            )

    async def chat_message(self, event):
        """Sends message to WebSocket"""
        await self.send(text_data=json.dumps(event))

    @sync_to_async
    def get_user(self, user_id):
        """Fetch user asynchronously"""
        try:
            return UserProfiles.objects.get(id=user_id)
        except UserProfiles.DoesNotExist:
            return None

    @sync_to_async
    def save_message(self, sender, receiver, content, conversation_id):
        """Save message in the database asynchronously"""
        return Message.objects.create(
            sender=sender,
            receiver=receiver,
            content=content,
            conversation_id=conversation_id
        )
