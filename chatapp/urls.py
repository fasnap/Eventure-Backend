# api/urls.py
from django.urls import path

from .views import ChatMessagesView, ChatRoomListView, CreateChatRoomView
urlpatterns = [
    path('list/', ChatRoomListView.as_view(), name='chat-list'),
    path('<int:room_id>/messages/', ChatMessagesView.as_view(), name='chat-messages'),
    path('create/', CreateChatRoomView.as_view(), name='create-chat'),
]