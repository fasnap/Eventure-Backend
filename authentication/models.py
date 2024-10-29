# api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class AccountUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('attendee', 'Attendee'),
        ('creator', 'Creator'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True)
    username=models.CharField(max_length=150, unique=True)
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    otp = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.email

class AttendeeProfile(models.Model):
    user=models.OneToOneField(AccountUser, on_delete=models.CASCADE)
    phone_number=models.CharField(max_length=15, blank=True, null=True)
    birthday=models.DateField(blank=True, null=True)
    address=models.CharField(max_length=255, blank=True, null=True)
    profile_picture=models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    def __str__(self):
        return self.user.email
    
class CreatorProfile(models.Model):
    user=models.OneToOneField(AccountUser, on_delete=models.CASCADE)
    phone_number=models.CharField(max_length=15)
    organisation_name=models.CharField(max_length=255)
    organisation_address=models.TextField()
    document_copy=models.FileField(upload_to='document_copies/')
    is_verified=models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.email