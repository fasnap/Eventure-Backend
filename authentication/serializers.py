# serializers.py
import random
from rest_framework import serializers
from .models import AccountUser, AttendeeProfile, CreatorProfile
from django.core.mail import send_mail
from decouple import config
from .tasks import send_otp_email 
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountUser
        fields = ('id', 'email', 'first_name', 'last_name', 'username', 'password', 'user_type', 'is_verified', 'is_active', 'created_at', 'updated_at')

        extra_kwargs = {'password': {'write_only': True}}

        
    def create(self, validated_data):
        user = AccountUser.objects.create_user(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        
        # Generate and send OTP
        otp = random.randint(100000, 999999)
        user.otp = otp
        user.save()
        subject = "OTP for Registration"
        message = "Your OTP for registration is "
        # Call Celery task to send OTP email
        send_otp_email.delay(user.email, otp, subject, message) 

        return user

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.IntegerField()


    def validate(self, attrs):
        try:
            user = AccountUser.objects.get(email=attrs['email'])
        except AccountUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        
        if user.otp != attrs['otp']:
            raise serializers.ValidationError('Invalid OTP')
        
        # Verify user and clear OTP
        user.is_verified = True
        user.is_active = True
        user.otp = None  # Clear OTP after verification
        user.save()
        return attrs

class CreatorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name=serializers.CharField(source='user.first_name',required=False)
    last_name=serializers.CharField(source='user.last_name',required=False)
    document_copy = serializers.FileField(required=False)   
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = CreatorProfile
        fields = ['id', 'email', 'first_name','last_name','phone_number', 'organisation_name', 'organisation_address', 'document_copy','is_verified', 'is_setup_submitted', 'profile_picture']
    def update(self, instance, validated_data):
        
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user.save()
        instance.save()
        return instance
   
    
class AttendeeProfileSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(source='user.email', read_only=True)
    first_name=serializers.CharField(source='user.first_name',required=False)
    last_name=serializers.CharField(source='user.last_name',required=False)
    # profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = AttendeeProfile
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'birthday', 'address']
    def update(self, instance, validated_data):
        # Update user fields (first_name, last_name)
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        
         # Update AttendeeProfile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.user.save()
        instance.save()
        return instance