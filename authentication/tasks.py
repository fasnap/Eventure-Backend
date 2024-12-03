# accounts/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_otp_email(user_email, otp, subject, message):
    message =  message+ " " + str(otp)
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user_email],
        fail_silently=False
    )
    return "OTP sent successfully"
