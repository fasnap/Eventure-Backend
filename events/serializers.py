from .models import Event
from rest_framework import serializers

class EventSerializer(serializers.ModelSerializer):
    date = serializers.DateField(input_formats=['%Y-%m-%d'])
    start_time = serializers.TimeField(input_formats=['%H:%M'])
    end_time = serializers.TimeField(input_formats=['%H:%M'])
    class Meta:
        model = Event
        fields = [
            'id', 'creator', 'title', 'category', 'event_type', 'date', 'start_time', 'end_time',
            'description', 'image', 'venue', 'country', 'state', 'district', 'is_created', 'is_approved', 'ticket_type', 'price', 'total_tickets', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['creator']
    def validate(self, data):
        user = self.context['request'].user
        if not user.creatorprofile.is_verified:
            raise serializers.ValidationError("Creator profile must be verified before creating an event.")
        data['is_approved']=False
        return data
    
class EventCategorySerializer(serializers.Serializer):
    value=serializers.CharField()
    label=serializers.CharField()
    