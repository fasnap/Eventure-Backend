# api/urls.py
from django.urls import path
from .views import UserCreate, VerifyOTPView, LoginView, CreatorAccountSetupView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', UserCreate.as_view(), name='user-register'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='user-login'),  # Added login URL
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('creator/setup/', CreatorAccountSetupView.as_view(), name='creator-account-setup')
]
