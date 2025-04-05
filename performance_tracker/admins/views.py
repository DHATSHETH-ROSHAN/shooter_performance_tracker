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

@login_required
def get_coach_details(request, coach_id):
    try:
        coach = UserProfiles.objects.get(id=coach_id)
        shooters=list(CoachShooterRelation.objects.filter(coach=coach, status="Accepted").values_list('shooter_id__username', flat= True))
        shooter_details = list(UserProfiles.objects.filter(username__in = shooters).values())
        male_shooters=CoachShooterRelation.objects.filter(coach=coach, status="Accepted", shooter__gender="Male").values()
        female_shooters=CoachShooterRelation.objects.filter(coach=coach, status="Accepted", shooter__gender="Female").values()
        data = {
            "username": coach.username,
            "email": coach.email,
            "mobile": coach.mobile_number,
            "gender":coach.gender,
            "experience": coach.years_of_experience,
            "specialization": coach.coaching_specialization,
            "shooters": shooters,
            "shooter_details" : shooter_details,
            "shooters_count":len(shooters),
            "male_shooters_count": male_shooters.count(),
            "female_shooters_count":female_shooters.count(),
        }
        return JsonResponse(data)
    except UserProfiles.DoesNotExist:
        return JsonResponse({"error": "Coach not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required    
def add_new_shooter(request):
    if request.method == "POST":
        # Get the form data
        staff = request.user
        print(staff)
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        date_of_birth = request.POST.get("dob")
        mobile_number = request.POST.get("mobile")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role")
        gender = request.POST.get("gender")
        coaching_specialization = None
        years_of_experience = None
        affiliated_club = staff.affiliated_club
        is_active = True
        is_superuser = False
        is_staff = False
        if not all([firstname, lastname, username, email, password1, password2]):  # Added validation for required fields
            messages.error(request, 'All fields are required!')
            return render(request, 'staffhome.html')
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'staffhome.html')
        elif UserProfiles.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'staffhome.html')
        elif UserProfiles.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'staffhome.html')
        else:
            hashed_pwd = make_password(password1)
            user = UserProfiles.objects.create(first_name=firstname, 
                                               last_name=lastname, 
                                                username=username,
                                                email=email,
                                               date_of_birth=date_of_birth, 
                                               mobile_number=mobile_number, 
                                               password=hashed_pwd, 
                                               role=role,
                                               gender=gender, 
                                               is_staff=is_staff, 
                                               is_active=is_active,
                                               is_superuser=is_superuser, 
                                               coaching_specialization=coaching_specialization,
                                               years_of_experience=years_of_experience,  # Save experience
            affiliated_club=affiliated_club )
        user.save()
        messages.success(request, 'Shooter added successfully!')
        return redirect('staff_home')
    return redirect('staff_home')

@login_required
def add_new_coach(request):
    if request.method == "POST":
        staff = request.user
        print(staff)
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        date_of_birth = request.POST.get("dob")
        mobile_number = request.POST.get("mobile")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        role = request.POST.get("role")
        gender = request.POST.get("gender")
        coaching_specialization = request.POST.get("specialization")
        experience = request.POST.get("experience")
        years_of_experience = int(experience) if experience and experience.isdigit() else 0
        affiliated_club = staff.affiliated_club
        is_active = False
        is_superuser = False
        is_staff = False
        required_fields = [firstname, lastname, username, email, password1, password2, date_of_birth, gender, mobile_number]
        if not all(required_fields): # Added validation for required fields
            messages.error(request, 'All fields are required!')
            return render(request, 'staffhome.html')
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'staffhome.html')
        elif UserProfiles.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'staffhome.html')
        elif UserProfiles.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'staffhome.html')
        else:
            hashed_pwd = make_password(password1)
            user = UserProfiles.objects.create(first_name=firstname, 
                                               last_name=lastname, 
                                                username=username,
                                                email=email,
                                               date_of_birth=date_of_birth, 
                                               mobile_number=mobile_number, 
                                               password=hashed_pwd, 
                                               role=role,
                                               gender=gender, 
                                               is_staff=is_staff, 
                                               is_active=is_active,
                                               is_superuser=is_superuser, 
                                               coaching_specialization=coaching_specialization,
                                               years_of_experience=years_of_experience,  # Save experience
            affiliated_club=affiliated_club )
        user.save()
        messages.success(request, 'Coach added successfully!')
        return redirect('staff_home')
    return redirect('staff_home')

# @login_required
# def shooter_coach_relationship(request):
    if request.method == "POST":
        shooter_id = request.POST.get("shooter_id")
        coach_id = request.POST.get("coach_id")
        action = request.POST.get("action")
        shooter = UserProfiles.objects.get(id=shooter_id)
        coach = UserProfiles.objects.get(id=coach_id)
        if action == "Accept":
            relation, created = CoachShooterRelation.objects.get_or_create(shooter=shooter, coach=coach, status="Accepted")
            if created:
                messages.success(request, 'Relationship accepted successfully!')
            else:
                messages.error(request, 'Relationship already exists!')
        elif action == "Reject":
            relation = CoachShooterRelation.objects.filter(shooter=shooter, coach=coach).first()
            if relation:
                relation.delete()
                messages.success(request, 'Relationship rejected successfully!')
            else:
                messages.error(request, 'No relationship found!')
    return redirect('staff_home')

@login_required
def coach_shooter_relation(request, coachId,):
    try:
        coachdetails = UserProfiles.objects.get(id=coachId)
        shooters = CoachShooterRelation.objects.filter(coach=coachId, status="Accepted").values_list('shooter_id__username', flat=True)
        available_shooters = UserProfiles.objects.filter(role="Shooter", affiliated_club = coachdetails.affiliated_club, coach_id__isnull= True).values_list('id','username' )
        print(available_shooters)
        data = {
            "id": coachdetails.id,
            "name": coachdetails.username,
            "email": coachdetails.email,
            "shooters": list(shooters),
            "shooter_count": len(shooters),
            "available_shooters": list(available_shooters)
        }
        return JsonResponse(data)
    except UserProfiles.DoesNotExist:
        return JsonResponse({"error": "Coach not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)






@login_required
def aassign_shooter_to_coach(request, coachId, shooterId):
    user_profile = request.user
    if request.method == "POST":
        coach = UserProfiles.objects.get(id=coachId)
        shooter = UserProfiles.objects.get(id=shooterId)
        print(shooter, coach)
        messages.success(request, 'Shooter added to coach successfully!!')
        return redirect('staff_home')










@login_required
def shooter_coach_relation(request, shooterId):
    try:
        shooter = UserProfiles.objects.get(id=shooterId)
        coaches = CoachShooterRelation.objects.filter(shooter=shooterId, status="Accepted").values_list('coach_id__username', flat=True)
        coaches_list = list(coaches)
        if not coaches_list:
            available_coaches = UserProfiles.objects.filter(role="Coach", affiliated_club=shooter.affiliated_club).exclude(id__in=coaches_list).values_list('username', flat=True)
            coaches = list(available_coaches)
        else:
            coaches = list(coaches)
        print(shooter, coaches)
        data = {
            "id": shooter.id,
            "name": shooter.username,
            "email": shooter.email,
            "coaches": list(coaches),
            "coaches_count": len(coaches),
        }
        return JsonResponse(data)
    except UserProfiles.DoesNotExist:
        return JsonResponse({"error": "Shooter not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)