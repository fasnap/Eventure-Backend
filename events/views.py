from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import EventSerializer
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Event

# Create your views here.
class EventCreateView(APIView):
    permission_classes = [IsAuthenticated]
   

    def post(self, request, *args, **kwargs):
    
        user=request.user
        if not user.creatorprofile.is_verified:
            raise ValueError("You must have a verified profile to create an event.")
       
        print("data in view of event ", request.data)
        serializer = EventSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(creator=user, is_created=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer validation errors:", serializer.errors)  # This will show the validation errors.
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventCategoryView(APIView):
    
    def get(self,request):
        categories=Event.EVENT_CATEGORY_CHOICES
        data=[{"value":value, "label":label} for value,label in categories]
     
        return Response(data)
    
class AttendeeEventsListView(APIView):
    permission_classes = [IsAuthenticated]
    
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
            
        serializer=EventSerializer(events, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class AttendeeSingleEventView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, event_id):
        try:
            event=Event.objects.get(id=event_id)
            serializer=EventSerializer(event)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Event.DoesNotExist:
            return Response({"error": "Event not found."}, status=status.HTTP_404_NOT_FOUND)
