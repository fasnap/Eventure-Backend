from attr import fields
from .models import Attendance, Event, EventRegistration, Feedback, Notification
from rest_framework import serializers
from django.db.models import Avg

class EventSerializer(serializers.ModelSerializer):
    date = serializers.DateField(input_formats=['%Y-%m-%d'])
    start_time = serializers.TimeField(input_formats=['%H:%M', '%I:%M %p'])
    end_time = serializers.TimeField(input_formats=['%H:%M', '%I:%M %p'])
    creator = serializers.CharField(source='creator.username', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'creator', 'title', 'category', 'event_type', 'date', 'start_time', 'end_time', 'creator_status', 'admin_status',
            'description', 'image', 'venue', 'country', 'state', 'district', 'is_created', 'is_approved', 'ticket_type', 'price', 'total_tickets', 
            'created_at', 'updated_at', 'latitude', 'longitude', 'location', 'meeting_link','is_streaming']
        read_only_fields = ['creator','is_streaming']
    def validate(self, data):
        user = self.context['request'].user
        if not user.creatorprofile.is_verified:
            raise serializers.ValidationError("Creator profile must be verified before creating an event.")
        print("data in serialier", data)
        # Validate for offline event, latitude and longitude are required
        if data['event_type'] == 'offline':
            if not data.get('latitude') or not data.get('longitude'):
                raise serializers.ValidationError("Latitude and Longitude are required for offline events.")
        
        if data['event_type'] == 'online':
            if data.get('venue'):
                raise serializers.ValidationError("Venue should not be provided for online events.")
            if data.get('latitude') or data.get('longitude'):
                raise serializers.ValidationError("Latitude and Longitude should not be provided for online events.")
        if 'image' in data and not hasattr(data['image'], 'file'):
            raise serializers.ValidationError("Invalid image file format.")
        data['is_approved']=False
        return data
    
class EventCategorySerializer(serializers.Serializer):
    value=serializers.CharField()
    label=serializers.CharField()
    
class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = ['attendee', 'ticket', 'event', 'payment_id', 'payment_status']
  
class AttendeeEventsSerializer(serializers.ModelSerializer):
    event=EventSerializer()
    qr_code_url = serializers.SerializerMethodField()
    class Meta:
        model = EventRegistration
        fields = ['event', 'attendee', 'ticket', 'qr_code_url', 'payment_status']  
        read_only_fields = ['attendee', 'ticket', 'payment_status']
    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class AttendanceSerializer(serializers.ModelSerializer):
    attendee_username = serializers.CharField(source="attendee.username", read_only=True)
    attendee_email = serializers.CharField(source="attendee.email", read_only=True)
    ticket_number=serializers.CharField(source="registration.ticket", read_only=True)
    class Meta:
        model = Attendance
        fields = ["id", "attendee", "event", "attendee_username", "attendee_email", "check_in_time", "is_present", "ticket_number"]

class EventUserRegistrationSerializer(serializers.ModelSerializer):
    attendee_username = serializers.CharField(source="attendee.username", read_only=True)
    attendee_email = serializers.CharField(source="attendee.email", read_only=True)
    class Meta:
        model = EventRegistration
        fields = ["id", "attendee", "attendee_username", "attendee_email", "event", "payment_id", "payment_status", "ticket", "created_at"]
    
class FeedbackSerializer(serializers.ModelSerializer):
    attendee_username=serializers.CharField(source="attendee.username", read_only=True)
    class Meta:
        model = Feedback
        fields = ['attendee','event','rating', 'comment', 'attendee_username']
        read_only_fields = ['attendee', 'event']
  
class StreamingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id', 'is_streaming', 'stream_started_at', 'stream_ended_at',
            'stream_key', 'viewer_count', 'stream_quality', 'enable_chat',
            'enable_recording', 'stream_duration'
        ]