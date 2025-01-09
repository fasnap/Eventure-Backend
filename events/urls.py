# api/urls.py
from django.urls import path
from .views import AllFeedbackView,AttendedEventsListView, EventAttendanceListView, EventRegisteredUsersListView, EventStatisticsView, EventUpdateStatusView, SubmitFeedbackView, UpdateFeedbackView, mark_attendance,CreateOrderView,NotificationListView,AttendeeRegisteredEventsAPIView, AttendeeSingleEventView, EventCreateView,AttendeeEventsListView, EventCategoryView, CreatorEventListView, MarkNotificationViewedView, RegisterForEventView, RegisterPaidEventView

urlpatterns = [
    path('create_event/', EventCreateView.as_view(), name='create-event'),
    path('creator/events/',CreatorEventListView.as_view(), name='ccreator-events-list'),
    path('event-categories/', EventCategoryView.as_view(), name='event-categories'),
    
    path('attendee/events/list/', AttendeeEventsListView.as_view(), name='attendee-events'),
    path('<int:event_id>/', AttendeeSingleEventView.as_view(), name='attendee-single-event'),
    path('<int:event_id>/register/', RegisterForEventView.as_view(), name='attendee-event-register'),
    path('attendee/registered_events/', AttendeeRegisteredEventsAPIView.as_view(), name='attendee-registered-events'),
    
    path('notifications/<int:notification_id>/mark_viewed/', MarkNotificationViewedView.as_view(), name='mark_notification_viewed'),
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    
    path('create-order/<int:event_id>/', CreateOrderView.as_view(), name='create_order'),
    path('registerPaidEvent/<int:event_id>/', RegisterPaidEventView.as_view(), name='register_paid_event'),
    path('mark-attendance/', mark_attendance, name='mark-attendance'),
    path('event-statistics/', EventStatisticsView.as_view(), name='event-statistics'),
    path('<int:event_id>/attendance/', EventAttendanceListView.as_view(), name='event_attendance'),
    path('<int:event_id>/registered_users/', EventRegisteredUsersListView.as_view(), name='registered_users'),
    path('<int:event_id>/update-status/', EventUpdateStatusView.as_view(), name='update_status'),
    path('attendee/attended_events/', AttendedEventsListView.as_view(), name='attended_events'),
    path('<int:event_id>/feedback/submit/', SubmitFeedbackView.as_view(), name='submit_feedback'),
    path('<int:feedback_id>/update/feedback/', UpdateFeedbackView.as_view(), name='update_feedback'),
    path('<int:event_id>/feedbacks/', AllFeedbackView.as_view(), name='all_feedbacks')



]