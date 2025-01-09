# urls.py
from django.urls import path
from .views import ChatGroupView, MessageListView
from . import views

urlpatterns = [
    path('chat-groups/', ChatGroupView.as_view(), name="chat-groups"),
    path('messages/<int:group_id>/', MessageListView.as_view(), name="group-messages"),
    path('api/upload/', views.upload_file, name='upload_file'),

]
