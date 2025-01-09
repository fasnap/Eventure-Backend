# api/urls.py
from django.urls import path
from .views import AdminDashboardView, AdminLoginView, ApprovedCreatorsListView, BlockUnblockUserView, CreatorProfileApprovalView, CreatorProfileListView, CreatorProfileRejectView, EventsListView, UsersListView, EventApprovalView, EventRejectView

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'), 
    
    path('creators/list/', CreatorProfileListView.as_view(), name='creator-list'),
    path('creators/approve/<int:pk>/', CreatorProfileApprovalView.as_view(), name='creator-approve'),
    path('creators/reject/<int:pk>/', CreatorProfileRejectView.as_view(), name='creator-reject'),
    path('approved-creators/',ApprovedCreatorsListView.as_view(), name='approved-creators'),
    
    path('users/list/', UsersListView.as_view(), name='users-list'),
    path('users/block_unblock/<int:user_id>/', BlockUnblockUserView.as_view(), name="block-unblock-user"),
    
    path('event/approve/<int:event_id>/', EventApprovalView.as_view(), name='approve-event'),
    path('event/reject/<int:event_id>/', EventRejectView.as_view(), name='reject-event'),
    path('event/list/', EventsListView.as_view(), name='events-list'),
    
    path('dashboard/', AdminDashboardView.as_view(), name='dashboard')
]
