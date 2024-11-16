# api/urls.py
from django.urls import path
from .views import AdminLoginView, ApprovedCreatorsListView, BlockUnblockUserView, CreatorProfileApprovalView, CreatorProfileListView, CreatorProfileRejectView, UsersListView

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'), 
    
    path('creators/list/', CreatorProfileListView.as_view(), name='creator-list'),
    path('creators/approve/<int:pk>/', CreatorProfileApprovalView.as_view(), name='creator-approve'),
    path('creators/reject/<int:pk>/', CreatorProfileRejectView.as_view(), name='creator-reject'),
    path('approved-creators/',ApprovedCreatorsListView.as_view(), name='approved-creators'),
    
    path('users/list/', UsersListView.as_view(), name='users-list'),
    path('users/block_unblock/<int:user_id>/', BlockUnblockUserView.as_view(), name="block-unblock-user")
]
