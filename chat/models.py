from events.models import Event
from django.db import models
from authentication.models import AccountUser

class ChatGroup(models.Model):
    name=models.CharField(max_length=250)
    event=models.OneToOneField(Event, on_delete=models.CASCADE, related_name="chat_group")
    owner=models.ForeignKey(AccountUser, on_delete=models.CASCADE, related_name="owned_groups")
    members=models.ManyToManyField(AccountUser, related_name="chat_groups")

    def __str__(self):
        return self.name
class Message(models.Model):
    group=models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name="messages")
    sender=models.ForeignKey(AccountUser, on_delete=models.CASCADE)
    content=models.TextField()
    timestamp=models.DateTimeField(auto_now_add=True)
    file = models.URLField(max_length=500, blank=True, null=True)  # URL to the file

    def __str__(self):
        return f"{self.sender.username}:{self.content[:20]}"