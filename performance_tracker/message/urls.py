from django.urls import path
from .views import chat_view, get_messages, mark_as_read

urlpatterns = [
    path("chat/<int:user_id>/", chat_view, name="chat_view"),
    path("messages/<str:conversation_id>/", get_messages, name="get_messages"),
    path("messages/read/<str:conversation_id>/", mark_as_read, name="mark_as_read"),
]
