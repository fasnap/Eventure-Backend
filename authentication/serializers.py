# api/serializers.py
import random
from rest_framework import serializers
from .models import AccountUser, CreatorProfile
from django.core.mail import send_mail

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountUser
        fields = ('id', 'email', 'first_name', 'last_name', 'username', 'password', 'user_type', 'is_verified')
        extra_kwargs = {'password': {'write_only': True}}
        
    def create(self, validated_data):
        user = AccountUser.objects.create_user(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        
        # Generate and send OTP
        otp = random.randint(100000, 999999)
        user.otp = otp
        user.save()
        send_mail(
            'Eventure OTP',
            f'Your OTP is {otp}',
            'eventureotp@gmail.com',
            [user.email],
            fail_silently=False,
        )
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
        user.otp = None  # Clear OTP after verification
        user.save()
        return attrs

class CreatorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = CreatorProfile
        fields = ['user_email', 'phone_number', 'organisation_name', 'organisation_address', 'document_copy','is_verified']