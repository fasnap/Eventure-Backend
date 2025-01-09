# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AccountUser, AttendeeProfile, CreatorProfile

@receiver(post_save, sender=AccountUser)
def create_attendee_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'attendee':
        AttendeeProfile.objects.create(user=instance)

@receiver(post_save, sender=AccountUser)
def create_creator_profile(sender, instance, created, **kwargs):
    if created and instance.user_type == 'creator':
        CreatorProfile.objects.create(user=instance)
