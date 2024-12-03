from .models import Event
from rest_framework import serializers

class EventSerializer(serializers.ModelSerializer):
    date = serializers.DateField(input_formats=['%Y-%m-%d'])
    start_time = serializers.TimeField(input_formats=['%H:%M', '%I:%M %p'])
    end_time = serializers.TimeField(input_formats=['%H:%M', '%I:%M %p'])
    creator = serializers.CharField(source='creator.username', read_only=True)
    class Meta:
        model = Event
        fields = [
            'id', 'creator', 'title', 'category', 'event_type', 'date', 'start_time', 'end_time',
            'description', 'image', 'venue', 'country', 'state', 'district', 'is_created', 'is_approved', 'ticket_type', 'price', 'total_tickets', 
            'created_at', 'updated_at', 'latitude', 'longitude', 'location']
        read_only_fields = ['creator']
    def validate(self, data):
        user = self.context['request'].user
        if not user.creatorprofile.is_verified:
            raise serializers.ValidationError("Creator profile must be verified before creating an event.")
        print("the dat in backedn is ",data)
        # Validate for offline event, latitude and longitude are required
        if data['event_type'] == 'offline':
            if not data.get('latitude') or not data.get('longitude'):
                raise serializers.ValidationError("Latitude and Longitude are required for offline events.")
         # Check the validity of the image file
        if 'image' in data:
            print("Image field data:", data['image'])
        if 'image' in data and not hasattr(data['image'], 'file'):
            raise serializers.ValidationError("Invalid image file format.")
        data['is_approved']=False
        return data
    
class EventCategorySerializer(serializers.Serializer):
    value=serializers.CharField()
    label=serializers.CharField()
    