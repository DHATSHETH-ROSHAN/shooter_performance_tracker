from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Message
from users.models import UserProfiles
from django.db.models import Q

@login_required
def chat_view(request, user_id):
    """Renders the chat interface between the logged-in user and another user"""
    other_user = get_object_or_404(UserProfiles, id=user_id)
    
    # Generate the conversation ID (same logic as in models.py)
    conversation_id = "_".join(sorted([str(request.user.id), str(other_user.id)]))
    
    # Fetch previous messages
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by("timestamp")
    return render(request, "message/chat_message.html", {
        "other_user": other_user,
        "messages": messages,
        "conversation_id": conversation_id
    })

@login_required
def get_messages(request, conversation_id):
    """Fetch previous messages for a given conversation ID (used for AJAX)"""
    messages = Message.objects.filter(conversation_id=conversation_id).order_by("timestamp")
    messages_data = [
        {
            "sender": msg.sender.username,
            "receiver": msg.receiver.username,
            "message": msg.content,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for msg in messages
    ]
    return JsonResponse({"messages": messages_data})

@login_required
def mark_as_read(request, conversation_id):
    """Mark all messages as read for the logged-in user"""
    Message.objects.filter(conversation_id=conversation_id, receiver=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "success"})
