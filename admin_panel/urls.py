# api/urls.py
from django.urls import path
from .views import AdminLoginView, CreatorProfileApprovalView, CreatorProfileListView, CreatorProfileRejectView

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'), 
    path('creators/', CreatorProfileListView.as_view(), name='creator-list'),
    path('creators/approve/<int:pk>/', CreatorProfileApprovalView.as_view(), name='creator-approve'),
    path('creators/reject/<int:pk>/', CreatorProfileRejectView.as_view(), name='creator-reject')
]
