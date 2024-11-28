# api/urls.py
from django.urls import path
from .views import EventCreateView,AttendeeEventsListView, EventCategoryView

urlpatterns = [
    path('create_event/', EventCreateView.as_view(), name='create-event'),
    path('event-categories/', EventCategoryView.as_view(), name='event-categories'),
    path('attendee/events/list/', AttendeeEventsListView.as_view(), name='attendee-events'),
]