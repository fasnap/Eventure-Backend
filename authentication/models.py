# api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

class BaseModel(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class AccountUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field is required")
        email=self.normalize_email(email)
        user=self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self.create_user(email, username, password, **extra_fields)
    
class AccountUser(AbstractUser, BaseModel):
    USER_TYPE_CHOICES = [
        ('attendee', 'attendee'),
        ('creator', 'creator'),
        ('admin', 'admin'),
    ]
    email = models.EmailField(unique=True)
    username=models.CharField(max_length=150, unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    otp = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    
    objects = AccountUserManager()
    
    def __str__(self):
        return self.email


class AttendeeProfile(BaseModel):
    user=models.OneToOneField(AccountUser, on_delete=models.CASCADE)
    phone_number=models.CharField(max_length=15, blank=True, null=True)
    birthday=models.DateField(blank=True, null=True)
    address=models.CharField(max_length=255, blank=True, null=True)
    # profile_picture=models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    def __str__(self):
        return self.user.email
    
class CreatorProfile(BaseModel):
    user=models.OneToOneField(AccountUser, on_delete=models.CASCADE, related_name="creatorprofile")
    phone_number=models.CharField(max_length=15)
    organisation_name=models.CharField(max_length=255)
    organisation_address=models.TextField()
    document_copy=models.FileField(upload_to='document_copies/')
    is_verified=models.BooleanField(default=False)
    is_setup_submitted=models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return self.user.email