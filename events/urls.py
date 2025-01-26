# api/urls.py
from django.urls import path
from .views import DeleteFeedbackView, mark_stream_attendance,AllFeedbackView,AttendedEventsListView, EventAttendanceListView, EventExportView, EventRegisteredUsersListView, EventReportView, EventStatisticsView, EventUpdateStatusView, StreamSignalingView, StreamingRoomView, SubmitFeedbackView, UpdateFeedbackView, mark_attendance,CreateOrderView,NotificationListView,AttendeeRegisteredEventsAPIView, AttendeeSingleEventView, EventCreateView,AttendeeEventsListView, EventCategoryView, CreatorEventListView, MarkNotificationViewedView, RegisterForEventView, RegisterPaidEventView

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
    path('mark-stream-attendance/', mark_stream_attendance, name='mark-stream-attendance'),
    path('event-statistics/', EventStatisticsView.as_view(), name='event-statistics'),
    path('<int:event_id>/attendance/', EventAttendanceListView.as_view(), name='event_attendance'),
    path('<int:event_id>/registered_users/', EventRegisteredUsersListView.as_view(), name='registered_users'),
    path('<int:event_id>/update-status/', EventUpdateStatusView.as_view(), name='update_status'),
    path('attendee/attended_events/', AttendedEventsListView.as_view(), name='attended_events'),
    path('<int:event_id>/feedback/submit/', SubmitFeedbackView.as_view(), name='submit_feedback'),
    path('feedback/<int:feedback_id>/update/', UpdateFeedbackView.as_view(), name='update_feedback'),
    path('<int:event_id>/feedbacks/', AllFeedbackView.as_view(), name='all_feedbacks'),
    path('event-report/', EventReportView.as_view(), name='event_report'),
    path('event-export/', EventExportView.as_view(), name='event_export'),
    path('<int:event_id>/stream/', StreamingRoomView.as_view(), name='streaming-room'),
    path('<int:event_id>/signal/', StreamSignalingView.as_view(), name='streaming-signal'),
    path('feedback/<int:feedback_id>/delete/', DeleteFeedbackView.as_view(), name='update_feedback'),


]