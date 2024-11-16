from authentication.models import AccountUser, BaseModel
from django.db import models

# Create your models here.
class Event(BaseModel):
    EVENT_CATEGORY_CHOICES=[
        ('technology', 'Technology'),
        ('arts', 'Arts'),
        ('sports', 'Sports'),
        ('health', 'Health'),
        ('food', 'Food'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other')
    ]
    
    EVENT_TYPE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        
    ]
    creator=models.ForeignKey(AccountUser, on_delete=models.CASCADE, related_name='events')
    title=models.CharField(max_length=255)
    category=models.CharField(max_length=25, choices=EVENT_CATEGORY_CHOICES)
    event_type=models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES)
    date=models.DateField()
    time=models.TimeField()
    duration=models.DurationField()
    description=models.TextField()
    image=models.ImageField(upload_to='event_images/')
    venue=models.CharField(max_length=250, blank=True, null=True)
    country=models.CharField(max_length=50)
    state=models.CharField(max_length=50)
    google_map_link=models.URLField(blank=True, null=True)
    
    # Geolocation fields for offline events
    latitude=models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude=models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    # Streaming specific fields for online events
    is_streaming=models.BooleanField(default=False)
    created_streaming_sessions=models.BooleanField(default=False)
    
    is_approved=models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    