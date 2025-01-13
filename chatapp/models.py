from django.db import models
from authentication.models import AccountUser, BaseModel
# Create your models here.
class ChatRoom(models.Model):
    attendee=models.ForeignKey(AccountUser, related_name='attendee_chats', on_delete=models.CASCADE)
    creator=models.ForeignKey(AccountUser, related_name='creator_chats', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
             
    def __str__(self):
        return f"Chat between {self.attendee.username} and {self.creator.username}"

class Message(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('read', 'Read'),
    )
    chat_room=models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender=models.ForeignKey(AccountUser, on_delete=models.CASCADE)
    content=models.TextField()
    timestamp=models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    
    def __str__(self):
        return f"Message from {self.sender.username}  at {self.timestamp}"