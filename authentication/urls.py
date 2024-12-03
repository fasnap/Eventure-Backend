# api/urls.py
from django.urls import path
from .views import AttendeeProfileView, ForgotPasswordRequestView, LogoutView, ResetPasswordView, UserCreate, VerifyOTPView, LoginView, CreatorAccountSetupView, VerifyOtpViewForgotPassword, GoogleAuthView, CreatorProfileView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', UserCreate.as_view(), name='user-register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='user-login'),  # Added login URL
    
    path('google-auth/', GoogleAuthView.as_view(), name='google-auth'),
    
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   
    path('creator/profile/', CreatorAccountSetupView.as_view(), name='creator-account-setup'),
    path('creator/profile/<int:id>/', CreatorProfileView.as_view(), name='creator-profile'),

    path('attendee/profile/', AttendeeProfileView.as_view(), name='attendee-profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordRequestView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('verify-otp-forgot-password/', VerifyOtpViewForgotPassword.as_view(), name='verify-otp-forgot-password'),
]
