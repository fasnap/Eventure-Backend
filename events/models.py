from io import BytesIO
from django.utils import timezone
import qrcode
from authentication.models import AccountUser, BaseModel
from django.db import models
from django.core.files.base import ContentFile
from datetime import datetime
from django.db import transaction

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
    
    TICKET_TYPE_CHOICES=[
        ('paid', 'Paid'),
        ('free', 'Free'),
    ]
    
    ADMIN_STATUS_CHOICES = [
        ('rejected', 'rejected'),
        ('approved', 'approved'),
        ('pending', 'pending'),
    ]
    
    CREATOR_STATUS_CHOICES = [
        ('created', 'created'),
        ('completed', 'completed'),
        ('pending', 'pending'),
        ('cancelled', 'cancelled'),
        ('upcoming', 'upcoming'),
        ('ongoing', 'ongoing'),
        ('expired', 'expired'),
    ]
    
    
    
    creator=models.ForeignKey(AccountUser, on_delete=models.CASCADE, related_name='events')
    title=models.CharField(max_length=255)
    category=models.CharField(max_length=25, choices=EVENT_CATEGORY_CHOICES)
    event_type=models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES)
    date=models.DateField()
    start_time=models.TimeField()
    end_time=models.TimeField()
    description=models.TextField()
    image=models.ImageField(upload_to='event_images/')
    venue=models.CharField(max_length=250, blank=True, null=True)
    country=models.CharField(max_length=50)
    state=models.CharField(max_length=50)
    district=models.CharField(max_length=50)
  
    location = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    is_created=models.BooleanField(default=False)
    is_approved=models.BooleanField(default=False)
    
    admin_status=models.CharField(max_length=100, choices=ADMIN_STATUS_CHOICES, null=True, blank=True, default='pending')
    creator_status=models.CharField(max_length=100, choices=CREATOR_STATUS_CHOICES, null=True, blank=True, default='pending')
    
    # For online event
    meeting_link = models.URLField(max_length=500, blank=True, null=True)
   
    
    # Ticket
    ticket_type=models.CharField(max_length=10, choices=TICKET_TYPE_CHOICES, default='free')
    price=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    total_tickets=models.PositiveIntegerField(default=100)
    
    is_streaming = models.BooleanField(default=False)
    stream_started_at = models.DateTimeField(null=True, blank=True)
    stream_ended_at = models.DateTimeField(null=True, blank=True)
    stream_key = models.CharField(max_length=100, unique=True, null=True, blank=True)
    viewer_count = models.PositiveIntegerField(default=0)
    max_viewers = models.PositiveIntegerField(default=100)
    stream_duration = models.DurationField(null=True, blank=True)
    
    # Optional fields for stream configuration
    stream_quality = models.CharField(
        max_length=20,
        choices=[
            ('low', '480p'),
            ('medium', '720p'),
            ('high', '1080p')
        ],
        default='medium'
    )
    enable_chat = models.BooleanField(default=True)
    enable_recording = models.BooleanField(default=False)

    def start_stream(self):
        from django.utils import timezone
        if not self.is_streaming:
            self.is_streaming = True
            self.stream_started_at = timezone.now()
            self.creator_status = 'ongoing'
            self.save()

    def end_stream(self):
        from django.utils import timezone
        if self.is_streaming:
            self.is_streaming = False
            self.stream_ended_at = timezone.now()
            self.stream_duration = self.stream_ended_at - self.stream_started_at
            self.creator_status = 'completed'
            self.save()

    def update_viewer_count(self, count):
        self.viewer_count = min(count, self.max_viewers)
        self.save()

    class Meta:
        # Add indexes for frequently queried fields
        indexes = [
            models.Index(fields=['is_streaming', 'creator_status']),
            models.Index(fields=['stream_started_at']),
        ]

    def __str__(self):
        return self.title
    

class EventRegistration(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    attendee = models.ForeignKey(AccountUser, on_delete=models.CASCADE, related_name="registered_events")
    ticket = models.CharField(max_length=50, unique=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default="pending", null=True, blank=True) 
    qr_code=models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    
    def save(self, *args, **kwargs):
        qr_data=f"Event: {self.event.title}, Attendee: {self.attendee.email}, Ticket ID : {self.ticket}"
        qr=qrcode.make(qr_data)
        
        qr_image=BytesIO()
        qr.save(qr_image, format='PNG')
        qr_image.seek(0)
        self.qr_code.save(f"{self.ticket}.png", ContentFile(qr_image.read()), save=False)
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.attendee.email} - {self.event.title}"

class Attendance(BaseModel):

    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendances')
    attendee=models.ForeignKey(AccountUser, on_delete=models.CASCADE, related_name='attended_events')
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, related_name="attendances")
    is_present=models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attendance for {self.attendee.email} at {self.event.title}"

class AttendanceManager:
    def scan_qr_and_mark_attendance(self, qr_code_data, event_id, event_creator):
        try:
            qr_code_data = qr_code_data.strip()
            print(f"Processed QR code data: {qr_code_data}")

            # Split QR code data into parts
            qr_parts = qr_code_data.split(', ')
            print("qr parts: ", qr_parts)
            # Validate the QR code data structure
            if len(qr_parts) != 3:
                return {"error": "Invalid QR code data format. Expected 3 parts."}
            
            
            # Extract event title, attendee email, and ticket ID
            
            event_title = qr_parts[0].split(': ')[1]
            print("event_title:", event_title)
            attendee_email = qr_parts[1].split(': ')[1]
            print("attendee_email:", attendee_email)
            ticket_id = qr_parts[2].split(': ')[1]
            print("ticket_id:", ticket_id)
        
            event = Event.objects.filter(id=event_id, creator=event_creator).first()

            if not event:
                return {"error": "Event not found or you don't have access to this event."}

            if event.title != event_title:
                return {"error": "QR code does not belong to this event."}

            # Check if the attendee is registered for the event
            registration = EventRegistration.objects.filter(event=event, attendee__email=attendee_email, ticket=ticket_id).first()
            if not registration:
                return {"error": "Attendee is not registered for this event."}

            # Mark the attendance
            attendance, created = Attendance.objects.get_or_create(
                event=event,
                attendee=registration.attendee,
                registration=registration
            )
            if attendance.is_present:
                return {"error": "Attendance already marked for this attendee."}

            
            attendance.is_present = True
            attendance.check_in_time = datetime.now()
            attendance.save()
            return {"success": "Attendance marked successfully."}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}
            

class Notification(models.Model):
    user=models.ForeignKey(AccountUser, on_delete=models.CASCADE)
    message=models.TextField()
    viewed=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.message
    
class Feedback(BaseModel):
    event=models.ForeignKey(Event, on_delete=models.CASCADE, related_name="feedbacks")
    attendee=models.ForeignKey(AccountUser, on_delete=models.CASCADE, related_name="feedbacks")
    rating=models.PositiveSmallIntegerField(default=0)
    comment=models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Feedback by {self.attendee.email} on {self.event.title}"

# class StreamSessions(models.Model):
#     STREAM_STATUS_CHOICES = [
#         ('active', 'Active'),
#         ('ended', 'Ended'),
#         ('failed', 'Failed'),
#     ]
#     event=models.ForeignKey(Event, on_delete=models.CASCADE)
#     started_at=models.DateTimeField(auto_now_add=True)
#     ended_at=models.DateTimeField(null=True, blank=True)
#     status=models.CharField(max_length=20, choices=STREAM_STATUS_CHOICES, default='active')
    
#     def __str__(self):
#         return f"Stream session for {self.event.title}"