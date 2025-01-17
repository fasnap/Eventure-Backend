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
    
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
    )
    chat_room=models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender=models.ForeignKey(AccountUser, on_delete=models.CASCADE)
    content=models.TextField()
    timestamp=models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    media_file=models.FileField(upload_to='chat_media/%y/%m/%d/', blank=True, null=True)
    media_type=models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file_name=models.CharField(max_length=255, blank=True, null=True)
    file_size=models.IntegerField(null=True, blank=True)
    def __str__(self):
        return f"Message from {self.sender.username}  at {self.timestamp}"

