from django.contrib import admin
from .models import Message, ChatGroup
# Register your models here.
admin.site.register(ChatGroup)
admin.site.register(Message)