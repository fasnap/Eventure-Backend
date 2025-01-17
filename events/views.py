import csv
from datetime import datetime
from functools import partial
from reportlab.lib.pagesizes import letter
from io import BytesIO
from re import L
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import uuid

import xlsxwriter
from .serializers import AttendanceSerializer,AttendeeEventsSerializer, EventRegistrationSerializer, EventSerializer, EventUserRegistrationSerializer, FeedbackSerializer, NotificationSerializer, StreamingSerializer
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Attendance, AttendanceManager, Event, EventRegistration, Feedback, Notification
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.pagination import PageNumberPagination
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import razorpay
import logging
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse
import json
from django.db.models import Count, Q
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


logger = logging.getLogger(__name__)

class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]
   

    def post(self, request, *args, **kwargs):
       
        user=request.user
        if not user.creatorprofile.is_verified:
            raise ValueError("You must have a verified profile to create an event.")
       
        serializer = EventSerializer(data=request.data, context={'request': request})
        print("Creating", request.data)
        if serializer.is_valid():
            event=serializer.save(creator=user, is_created=True)
            event.creator_status='created'
            event.save()
            # Send notification to admin group after the event is created
            channel_layer = get_channel_layer()
            message = f"New event '{event.title}' is waiting for admin approval."
            # Create a notification in the database for the admin
            notification = Notification.objects.create(
                user_id=user.id,  # Assuming the admin has an `id`
                message=message
            )
            
            async_to_sync(channel_layer.group_send)(
                'admin_notifications',  # The group name
                {
                    'type': 'send_notification',
                    'message': message,
                    'notification_id': notification.id
                 }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)  
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreatorEventListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user=request.user
        events=Event.objects.filter(creator=user)
        serializer=EventSerializer(events, many=True)
        return Response(serializer.data)
    
class EventCategoryView(APIView):
    
    def get(self,request):
        categories=Event.EVENT_CATEGORY_CHOICES
        data=[{"value":value, "label":label} for value,label in categories]
     
        return Response(data)

class EventPagination(PageNumberPagination):
    page_size = 6  # Items per page
    page_size_query_param = 'page_size'
    max_page_size = 50
     
class AttendeeEventsListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = EventPagination
    def get(self, request):
        current_date=timezone.now().date()
        current_time=timezone.now().time()
        events=Event.objects.filter(date__gte=current_date, is_approved=True).exclude(date=current_date, start_time__lt=current_time)
        
       
        min_price=request.query_params.get('min_price')
        max_price=request.query_params.get('max_price')
        start_date=request.query_params.get('start_date')
        end_date=request.query_params.get('end_date')
        event_type=request.query_params.get('event_type')
        sort_by=request.query_params.get('sort_by')
        
  
        if min_price and max_price:
            events=events.filter(price__gte=min_price, price__lte=max_price)
        elif min_price:
            events=events.filter(price__gt=min_price)
        elif max_price:
            events=events.filter(price__lte=max_price)
        
        if start_date and end_date:
            events=events.filter(date__range=[start_date, end_date])
        elif start_date:
            events=events.filter(date__gte=start_date)
        elif end_date:
            events=events.filter(date__lte=end_date)
        
        if event_type:
            events=events.filter(event_type__icontains=event_type)
        
        if sort_by == 'newest':
            events=events.order_by('-created_at')
        elif sort_by == 'a-z':
            events=events.order_by('title')
        elif sort_by == 'z-a':
            events=events.order_by('-title')
        elif sort_by == 'price_high-to-low':
            events=events.order_by('-price')
        elif sort_by == 'price_low_to_high':
            events=events.order_by('price')
        else:
            events=events.order_by('date')
        
        paginator=self.pagination_class()
      
        result_page = paginator.paginate_queryset(events, request)
        serializer=EventSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
        # serializer=EventSerializer(page, many=True)

        # return paginator.get_paginated_response(serializer.data)

class AttendeeSingleEventView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event=Event.objects.get(id=event_id)
            is_registered = EventRegistration.objects.filter(event=event, attendee=request.user).exists()

            serializer=EventSerializer(event)
            event_data = serializer.data
            event_data['is_registered'] = is_registered  # Add registration status

            return Response(event_data, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

class RegisterForEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        try:
            
            event = Event.objects.get(id=event_id, ticket_type="free")
            if event.total_tickets <= 0:
                return Response({"error": "No tickets available."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already registered
            if EventRegistration.objects.filter(event=event, attendee=request.user).exists():
                return Response({"error": "Already registered for this event."}, status=status.HTTP_400_BAD_REQUEST)
            print(request.data)
            registration_data = {
                "attendee": request.user.id,  # Ensure the correct user ID is passed
                "event": event.id,  # Ensure the correct event ID is passed
                "ticket": str(uuid.uuid4()), # Generate a unique ticket
                "payment_status": "free"
            }

            # Create Registration
            serializer = EventRegistrationSerializer(data=registration_data, context={'request': request})
           
            if serializer.is_valid():
                registration = serializer.save()
                send_mail(
                    subject="Event Registration Successful",
                    message=f"Thank you for registering for {event.title}.",
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                # Decrement ticket count
                event.total_tickets -= 1
                event.save()
               
                return Response({"message": "Successfully registered!"}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Event.DoesNotExist:
            return Response({"error": "Event not found or not free."}, status=status.HTTP_404_NOT_FOUND)

class AttendeeRegisteredEventsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user=request.user
        registrations=EventRegistration.objects.filter(attendee=user)
        serializer=AttendeeEventsSerializer(registrations, many=True)
        return Response(serializer.data)
    
class MarkNotificationViewedView(APIView):
    permission_classes=[IsAuthenticated]
    
    def post(self, request, notification_id):
        notification=Notification.objects.get(id=notification_id)
        notification.viewed=True
        notification.save()
        return Response({"message": "Notification viewed."}, status=status.HTTP_200_OK)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
   
    def get(self, request):
        notifications = Notification.objects.all()
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
class CreateOrderView(APIView):
    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id, ticket_type="paid")
            print("event is ", event.ticket_type, event.price)
            amount=int(event.price * 100)
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            print(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET )
            try:
                payment = client.order.create({
                    "amount": amount,
                    "currency": "INR",
                    "payment_capture": 1,
                })
                return Response(
                {
                    "order_id": payment["id"],
                    "amount": amount,
                    "name": request.user.username,
                    "email": request.user.email,
                },status=status.HTTP_200_OK,
            )
            except Exception as e:
                logger.error(f"Razorpay order creation failed: {str(e)}")
                return Response({"error": "Failed to create Razorpay order."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
        except Event.DoesNotExist:
            return Response({"error": "Event not found or not paid."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class RegisterPaidEventView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id, ticket_type="paid")
            if event.total_tickets <= 0:
                return Response({"error": "No tickets available."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user is already registered
            if EventRegistration.objects.filter(event=event, attendee=request.user).exists():
                return Response({"error": "Already registered for this event."}, status=status.HTTP_400_BAD_REQUEST)

            # Check for payment details
            payment_id = request.data.get("payment_id")
            order_id = request.data.get("order_id")
            if not payment_id or not order_id:
                return Response({"error": "Payment details missing."}, status=status.HTTP_400_BAD_REQUEST)
            
             # Fetch payment details from Razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            try:
                payment_details = client.payment.fetch(payment_id)
                payment_status = payment_details.get("status")
                if payment_status != "captured":
                    return Response({"error": "Payment not verified."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "Payment verification failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            registration = EventRegistration.objects.create(
                event=event,
                attendee=request.user,
                ticket=str(uuid.uuid4()),  # You can generate a unique ticket code
                payment_id=payment_id,  # Save the Razorpay payment ID
                payment_status=payment_status,
            )
            
             # Send email notification
            send_mail(
                subject="Event Registration Successful",
                message=f"Thank you for registering for {event.title}.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            
            # Decrement ticket count
            event.total_tickets -= 1
            event.save()
       
            return Response({"message": "Successfully registered!"}, status=status.HTTP_201_CREATED)

        except Event.DoesNotExist:
            return Response({"error": "Event not found or not paid."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST']) 
def mark_attendance(request):
    try:
        # Ensure we parse the incoming JSON body
        data = json.loads(request.body)
        qr_code_data = data.get('qr_code_data')
        event_id = data.get('eventId')
        if not qr_code_data or not event_id:
            return JsonResponse({"error": "QR code data or event ID is missing."}, status=400)
        event_creator=request.user
        manager=AttendanceManager()
        result=manager.scan_qr_and_mark_attendance(qr_code_data, event_id, event_creator)
        if "error" in result:
            return JsonResponse(result, status=400)
        return JsonResponse(result, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

class EventStatisticsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,*args, **kwargs):
        user=request.user
        total_events=Event.objects.filter(creator=user).count()
        waiting_approval_events=Event.objects.filter(creator=user, is_approved=False).count()
        
        rejected_events=Event.objects.filter(creator=user, is_approved=False).count()
        
        
        # Total registered attendees for each event
        event_stats = Event.objects.filter(creator=user).annotate(
            total_registered=Count('registrations'),
            total_attended=Count('attendances', filter=Q(attendances__is_present=True))
        ).values('title', 'total_registered', 'total_attended', 'creator_status', 'admin_status')

        # Total events created each month
        monthly_event_stats = Event.objects.filter(creator=user).values('date__year', 'date__month').annotate(
            total_events_per_month=Count('id')
        ).order_by('date__year', 'date__month')
        

        stats = {
            'rejected_events':rejected_events,
            'waiting_approval_events':waiting_approval_events,
            'total_events': total_events,
            'event_stats': event_stats,
            'monthly_event_stats': monthly_event_stats
        }

        return Response(stats, status=status.HTTP_200_OK)
    
class EventAttendanceListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, event_id):
        print("event_id", event_id)
        try:
            event=get_object_or_404(Event, id=event_id)
            if event.creator != request.user:
                return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)
            attendance_data = Attendance.objects.filter(event=event)
            serializer=AttendanceSerializer(attendance_data, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class EventRegisteredUsersListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event=get_object_or_404(Event, id=event_id)
            if event.creator != request.user:
                return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)
            registered_users = EventRegistration.objects.filter(event=event)
            serializer=EventUserRegistrationSerializer(registered_users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EventRegistration.DoesNotExist:
            return Response({"error": "Event not found or no registrations found."}, status=status.HTTP_404_NOT_FOUND)
        
class EventUpdateStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, event_id):
        try:
            event=Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if event.creator.id != request.user.id:
            return Response({"error": "Unauthorized access."}, status=status.HTTP_403_FORBIDDEN)
        new_status=request.data.get("status")

        
        if new_status == "ongoing":
            event_date = event.date
            if event_date != date.today():
                return Response({"error": "Event date must be today to mark as ongoing."}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status == "completed" and event.creator_status != "ongoing":
            return Response({"error": "Cannot complete an event that is not ongoing."}, status=status.HTTP_400_BAD_REQUEST)
        if new_status == "ongoing" and event.creator_status != "upcoming":
            return Response({"detail": "Event must be upcoming to mark as ongoing."}, status=status.HTTP_400_BAD_REQUEST)
        print("new status is ",new_status)
        event.creator_status = new_status
        event.save()
        return Response({"detail": f"Event status updated to {new_status}"}, status=status.HTTP_200_OK)

class AttendedEventsListView(APIView):
    parser_classes=[IsAuthenticated]
    
    def get(self, request):
        user=request.user
        attendances=Attendance.objects.filter(attendee=user, is_present=True)
        events=[attendance.event for attendance in attendances]
        serializer=EventSerializer(events, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class SubmitFeedbackView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, event_id):
        attendee=request.user
        try:
            event=Event.objects.get(id=event_id)
            print("event ", event)
            attendance=Attendance.objects.filter(event=event, attendee=attendee, is_present=True).exists()
            if not attendance:
                return Response({"error":"You can only provide feedback for attended events."}, status=status.HTTP_400_BAD_REQUEST)
            existing_feedback = Feedback.objects.filter(event=event, attendee=attendee).first()
            if existing_feedback:
                return Response({"error": "You have already submitted feedback for this event."}, status=status.HTTP_400_BAD_REQUEST)
            serializer=FeedbackSerializer(data=request.data)
            print("data-----  ", serializer)
            rating = request.data.get('feedback', {}).get('rating')
            comment = request.data.get('feedback', {}).get('comment')

            if serializer.is_valid():
                serializer.save(event=event, attendee=attendee, comment=comment,rating=rating)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

class UpdateFeedbackView(APIView):
    permission_classes=[IsAuthenticated]
    def put(self, request, feedback_id):
        attendee=request.user   
        try:
            feedback=Feedback.objects.get(id=feedback_id, attendee=attendee)
            serializer=FeedbackSerializer(feedback, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Feedback.DoesNotExist:
            return Response({"error": "Feedback not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)

class AllFeedbackView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, event_id):
        try:
            event=Event.objects.get(id=event_id)
            feedback=Feedback.objects.filter(event=event)
            serializer=FeedbackSerializer(feedback, many=True)
            
            
            print("feedbacks are--------------", serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
        
class EventReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        creator = request.user
        events = Event.objects.filter(creator=creator)
        
        title = request.GET.get('title', '')
        category = request.GET.get('category', '')
        status = request.GET.get('status', '')
        
        # Filter
        if title:
            events = events.filter(title__icontains=title)
        if category:
            events = events.filter(category__icontains=category)
        if status:
            events = events.filter(creator_status=status)
        
        #Sorting
        sort_by = request.GET.get('sort_by', 'date')
        if sort_by:
            events = events.order_by(sort_by)
            
        event_data = []
        for event in events:
            registered_count = EventRegistration.objects.filter(event=event).count()
            attended_count = Attendance.objects.filter(event=event, is_present=True).count()
            event_data.append({
                'title': event.title,
                'category': event.category,
                'date': event.date,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'status': event.creator_status,
                'ticket_type':event.ticket_type,
                'price':event.price,
                'registered_attendees':registered_count,
                'attended_attendees': attended_count,
            })
        
        return Response({'events': event_data})
        
    def export_to_csv(self, request):
        creator=request.user
        events=Event.objects.filter(creator=creator)
        response=HttpResponse(content_type='text/csv')
        response['Content-Disposition']='attachment; filename="event_report.csv"'
        writer=csv.writer(response)
        writer.writerow(['Title', 'Category', 'Date', 'Start Time', 'End Time', 'Status', 'Ticket Type', 'Price', 'Registered Attendees', 'Attended Attendees'])
        
        for event in events:
            registered_count=EventRegistration.objects.filter(event=event).count()
            attended_count=Attendance.objects.filter(event=event, is_present=True).count()
            writer.writerow([event.title, event.category, event.date, event.start_time, event.end_time, event.creator_status, event.ticket_type, event.price, registered_count, attended_count])
        return response
    def export_to_excel(self, request):
        creator = request.user
        events = Event.objects.filter(creator=creator)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        worksheet.write_row(0, 0, ['Title', 'Category', 'Date', 'Start Time', 'End Time', 'Status', 'Ticket Type', 'Price', 'Registered Attendees', 'Attended Attendees'])

        row = 1
        for event in events:
            registered_count = EventRegistration.objects.filter(event=event).count()
            attended_count = Attendance.objects.filter(event=event, is_present=True).count()
            worksheet.write_row(row, 0, [
                event.title,
                event.category,
                event.date,
                event.start_time,
                event.end_time,
                event.creator_status,
                event.ticket_type,
                event.price,
                registered_count,
                attended_count,
            ])
            row += 1

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="event_report.xlsx"'
        return response

    def export_to_pdf(self, request):
        creator = request.user
        events = Event.objects.filter(creator=creator)
        
        # Create the PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Prepare the data
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=34,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.gray,
            alignment=1,  # Center alignment
            spaceAfter=20,
        )
        
        elements.append(Paragraph('Event Report', title_style))
        elements.append(Paragraph(f'Generated on {datetime.now().strftime("%B %d, %Y")}', subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Prepare table data
        headers = ['Title', 'Category', 'Date', 'Start Time', 'End Time', 
                'Status', 'Ticket Type', 'Price', 'Registered', 'Attended']
        
        data = [headers]
        
        for event in events:
            registered_count = EventRegistration.objects.filter(event=event).count()
            attended_count = Attendance.objects.filter(event=event, is_present=True).count()
            time_str = f"{event.start_time.strftime('%H:%M')}-{event.end_time.strftime('%H:%M')}"

            data.append([
                Paragraph(event.title, styles['Normal']),  # Allow title to wrap
                event.category,
                event.date.strftime('%Y-%m-%d'),
                time_str,
                event.creator_status,
                event.ticket_type,
                f"${event.price}" if event.price else "Free",
                str(registered_count),
                str(attended_count)
            ])
        
        page_width = A4[0] - doc.leftMargin - doc.rightMargin
        col_widths = [
            page_width * 0.25,  # Title (25%)
            page_width * 0.12,  # Category
            page_width * 0.12,  # Date
            page_width * 0.12,  # Time
            page_width * 0.10,  # Status
            page_width * 0.10,  # Type
            page_width * 0.07,  # Price
            page_width * 0.06,  # Registered
            page_width * 0.06   # Attended
        ]
    
        # Create table with specific column widths
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Style the table
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Cell styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-2, 0), (-1, -1), 'CENTER'),  # Center align the last two columns
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            
            # Row styling
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            
            # Padding
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
    
        elements.append(table)
    
        # Add footer with page numbers
        def add_page_number(canvas, doc):
            page_num = canvas.getPageNumber()
            text = f"Page {page_num}"
            canvas.saveState()
            canvas.setFont('Helvetica', 9)
            canvas.drawRightString(A4[0] - 2*cm, 2*cm, text)
            canvas.restoreState()
        
        # Build PDF
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="event_report.pdf"'
        
        return response
class EventExportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        export_type = request.GET.get('export_type', 'csv')
        
        if export_type == 'csv':
            return EventReportView().export_to_csv(request)
        elif export_type == 'xlsx':
            return EventReportView().export_to_excel(request)
        elif export_type == 'pdf':
            return EventReportView().export_to_pdf(request)
        else:
            return Response({'error': 'Invalid export type.'}, status=status.HTTP_400_BAD_REQUEST)

class StreamingRoomView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
            
            is_creator=event.creator==request.user
            if is_creator:
                # Start the stream when creator joins
                event.start_stream()
            serializer = StreamingSerializer(event)
                
            is_attendee = EventRegistration.objects.filter(
                attendee=request.user,
                event=event
            ).exists() 
                       
            if not is_creator and not is_attendee:
                return Response({'error': 'You are not authorized to join this event.'}, status=status.HTTP_403_FORBIDDEN)
       
            room_data={
                'event_id': str(event.id),
                'user_id': str(request.user.id),
                'is_creator': is_creator,
                'stream_data': serializer.data 
            }
            print("room data", room_data)
            return Response(room_data, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
            if event.creator == request.user:
                event.end_stream()
                serializer = StreamingSerializer(event)
                return Response(serializer.data)
            return Response(
                {'error': 'Only creator can end stream'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        except Event.DoesNotExist:
            return Response(
                {'error': 'Event not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
class StreamSignalingView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
            signal_type=request.data.get('type')
            target_id=request.data.get('target')
            
            channel_layer=get_channel_layer()
            
            async_to_sync(channel_layer.group_send)(
                f'stream_{event_id}',
                {
                    'type':'streaming_signal',
                    'sender_id': str(request.user.id),
                    'target_id': target_id,
                    'signal_data':request.data
                }
            )
            return Response({'status':'signal sent'}, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)    