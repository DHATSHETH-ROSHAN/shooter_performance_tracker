from django.db import models

from django.db import models
from users.models import *
from scores.models import *
class Message(models.Model):
    sender = models.ForeignKey(UserProfiles, related_name="sent_messages", on_delete=models.CASCADE, db_index=True)
    receiver = models.ForeignKey(UserProfiles, related_name="received_messages", on_delete=models.CASCADE, db_index=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Conversation ID to group messages between a coach and a shooter
    conversation_id = models.CharField(max_length=255, db_index=True)
    # New field: Track if the message has been read
    is_read = models.BooleanField(default=False, db_index=True)

    def save(self, *args, **kwargs):
        """Auto-generate a unique conversation ID for the sender-receiver pair"""
        self.conversation_id = "_".join(sorted([str(self.sender.id), str(self.receiver.id)]))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:20]}..."
