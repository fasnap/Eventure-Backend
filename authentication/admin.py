from django.contrib import admin
from .models import AccountUser,CreatorProfile,AttendeeProfile
# Register your models here.
admin.site.register(AccountUser)
admin.site.register(AttendeeProfile)
admin.site.register(CreatorProfile)