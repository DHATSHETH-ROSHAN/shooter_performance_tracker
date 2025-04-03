from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Q
from users.models import *
from scores.models import *
from django.http import JsonResponse
# models import
from .models import *
from message.models import *
# modules
from datetime import datetime
from users.views import *

@login_required
def staff_home(request):
    if request.user.role == "Staff" and request.user.permitted == "Yes":
        userprofile = request.user
        profile_id = userprofile.id
        club_students = UserProfiles.objects.filter(Q(affiliated_club = userprofile.affiliated_club) & Q(role ="Shooter"))
        club_coaches = UserProfiles.objects.filter(Q(affiliated_club = userprofile.affiliated_club) & Q(role="Coach"))
        club_staff = UserProfiles.objects.filter(Q(affiliated_club = userprofile.affiliated_club) & Q(role="Staff"))
        students_count = club_students.count() if club_students.exists() else 0
        coaches_count =club_coaches.count() if club_coaches.exists() else 0
        staff_count = club_staff.count() if club_staff.exists() else 0
        # established calculation
        current_year = datetime.now().year
        established = current_year - (request.user.years_of_experience)
        staff = request.user
        try:
            staff_profile = UserProfiles.objects.get(role='Staff')
            same_club_users = UserProfiles.objects.filter(affiliated_club=staff_profile.affiliated_club).exclude(role='Staff')
        except UserProfiles.DoesNotExist:
            same_club_users = []
        chats = Message.objects.filter(Q(sender=staff) | Q(receiver=staff)).order_by('-timestamp')
    
        conversations = {}
        for msg in chats:
            other_user = msg.receiver if msg.sender == staff else msg.sender
            convo_id = f"{staff.id}_{other_user.id}" if staff.id < other_user.id else f"{other_user.id}_{staff.id}"

            if convo_id not in conversations:
                conversations[convo_id] = {
                    "otheruser": other_user,
                    "last_message" : msg,
                    "unread_count": Message.objects.filter(receiver=staff, sender=other_user, is_read=False).count()
                }

        for user in same_club_users:
            convo_id = f"{staff.id}_{user.id}" if staff.id < user.id else f"{user.id}_{staff.id}"
            if convo_id not in conversations:
                conversations[convo_id] = {
                    "other_user":user,
                    "last_message" :None, 
                    "unread_count": 0,
                }

        context = {
            'userprofile' : userprofile,
            'profile_id': profile_id,
            'club_students': club_students,
            'club_coaches' : club_coaches,
            'club_staff': club_staff,
            'students_count': students_count,
            'coaches_count' : coaches_count,
            'staff_count' :staff_count,
            'conversations' :conversations.values(),
        }
        
        return render(request, 'admin/staffhome.html', context)
    else:
        messages.error(request, "You are not allowed to vsit this page!!")
        return render(request, "home.html")
    
@login_required
def get_shooter_details(request, shooter_id):
    try:
        shooter = UserProfiles.objects.get(id=shooter_id)
        manual_scores = list(manualscore.objects.filter(user_profile_id=shooter).order_by('-date')[:3].values('date','match_type','s1t','s2t','s3t','s4t','s5t','s6t','total','average','duration'))
        est_scores = list(pdfScore.objects.filter(user_profile_id=shooter).order_by('-date')[:3].values('date','match_type','s1t','s2t','s3t','s4t','s5t','s6t','total','average_shot_score','average_series_score','duration'))
        coach_relation = CoachShooterRelation.objects.filter(shooter=shooter, status="Accepted").first()
        if coach_relation:
            coach_name = coach_relation.coach.username
        else:
            coach_name = None        
        data = {
            "username": shooter.username,
            "email": shooter.email,
            "mobile":shooter.mobile_number,
            "category": shooter.category,
            "gender": shooter.gender,
            "manual_scores": manual_scores,
            "est_scores":est_scores,
            "coach_name":coach_name,
        }
        return JsonResponse(data)
    except UserProfiles.DoesNotExist:
        return JsonResponse({"error": "Coach not found"}, status= 404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def get_coach_details(request, coach_id):
    try:
        coach = UserProfiles.objects.get(id=coach_id)
        shooters=CoachShooterRelation.objects.filter(coach=coach, status="Accepted")
        male_shooters=CoachShooterRelation.objects.filter(coach=coach, status="Accepted", shooter__gender="Male")
        female_shooters=CoachShooterRelation.objects.filter(coach=coach, status="Accepted", shooter__gender="Female")
        
        data = {
            "username": coach.username,
            "email": coach.email,
            "mobile": coach.mobile_number,
            "gender":coach.gender,
            "experience": coach.years_of_experience,
            "specialization": coach.coaching_specialization,
            "shooters_count":shooters.count(),
            "male_shooters_count": male_shooters.count(),
            "female_shooters_count":female_shooters.count(),
        }
        return JsonResponse(data)
    except UserProfiles.DoesNotExist:
        return JsonResponse({"error": "Coach not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)