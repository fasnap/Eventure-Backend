from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from .models import Event, EventRegistration
from django.core.mail import send_mail

@shared_task
def send_email_reminders():
    tomorrow=datetime.now() + timedelta(days=1)
    events=Event.objects.filter(date=tomorrow.date())

    for event in events:
        registrations=EventRegistration.objects.filter(event=event)
        for registration in registrations:
            # Send email reminder to the registered user
            send_mail(
                subject=f"Reminder : {event.title} is happening tomorrow!",
                message=f"Hi {registration.attendee.username},\n\n This is a friendly reminder about the event '{event.title}' scheduled for {event.date} at {event.location}. We hope to see you there!\n\n Best regards,\n Event Team",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[registration.attendee.email],
                fail_silently=False
            )
    