
from django.contrib import admin
from .models import Attendance, Event, EventRegistration, Feedback, Notification

# Register your models here.
admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Notification)
admin.site.register(Attendance)
admin.site.register(Feedback)