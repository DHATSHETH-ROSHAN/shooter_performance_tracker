from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.contrib import messages
from django.db.models import Q
from users.models import *
from django.utils.timezone import now
from users.forms import EventForm
from scores.models import *
from django.http import JsonResponse
# models import
from .models import *
from message.models import *
# modules
from datetime import datetime
from users.views import *
import json

@login_required
def staff_home(request):
    if request.user.role == "Staff" and request.user.permitted == "Yes":
        userprofile = request.user
        profile_id = userprofile.id
        print(profile_id)
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
            staff_profile = request.user
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
                    "other_user": other_user,
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

        events = Event.objects.filter(visibility__in=['coach', 'both'], date__gte=now().date()).order_by('date')
        formevent = EventForm()
        if request.method == "POST" and "event_submit" in request.POST:
            formevent = EventForm(request.POST)
            if formevent.is_valid():
                event = formevent.save(commit=False)
                event.created_by = request.user
                event.save()
                formevent.save_m2m()  # Save the many-to-many relationship
                messages.success(request, "Event created successfully!")
                return redirect("staff_home")
            else:
                messages.error(request, "There was a problem saving the event.")
        else:
            formevent = EventForm()

        
        print(events)
        context = {
            'userprofile' : userprofile,
            'profile_id': profile_id,
            'events': events, 
            'formevent': formevent,
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
def aassign_shooter_to_coach(request):
    try:
        data = json.loads(request.body)
        coach_id = data.get('coach_id')
        shooter_ids = data.get('shooter_ids', [])

        coach = UserProfiles.objects.get(id=coach_id)

        for shooter_id in shooter_ids:
            shooter = UserProfiles.objects.get(id=shooter_id)
            CoachShooterRelation.objects.get_or_create(coach=coach, shooter=shooter, status = "Accepted")
            Message.objects.create(sender=coach, receiver=shooter, content="Welcome!, You are now connected for training. Let's start practicing.")
            shooter.coach_id = coach.id
            shooter.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def remove_shooter_from_coach(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            coach_id = data.get('coach_id')
            shooter_username = data.get('shooter_username')

            coach = UserProfiles.objects.get(id=coach_id)
            shooter = UserProfiles.objects.get(username=shooter_username)

            CoachShooterRelation.objects.filter(coach=coach, shooter=shooter).delete()

            shooter.coach_id = None
            shooter.save()
            return JsonResponse({'Success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
  
@login_required
def shooter_coach_relation(request, shooterId):
    try:
        shooter = UserProfiles.objects.get(id=shooterId)
        relation = CoachShooterRelation.objects.filter(shooter=shooter, status="Accepted").select_related('coach').first()
        assigned_coach = relation.coach if relation else None
        data = {
            'shooter': {
                'id': shooter.id,
                'username': shooter.username,
                'email': shooter.email,
                'category': shooter.category,
            },
            'coach': {
                'id': assigned_coach.id,
                'username': assigned_coach.username,
            } if assigned_coach else None
        }
        return JsonResponse(data)
    except UserProfiles.DoesNotExist:
        return JsonResponse({"error": "Shooter not found"}, status= 404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status= 500)

@login_required
def available_coaches(request):
    coaches = UserProfiles.objects.filter(role='Coach')
    coach_list = [{'id': coach.id, 'username': coach.username} for coach in coaches]
    return JsonResponse({'coaches': coach_list})
   
@login_required
def assign_coach(request, coach_id, shooter_id):
    if request.method == 'POST':
        coach = get_object_or_404(UserProfiles, id=coach_id, role='Coach')
        shooter = get_object_or_404(UserProfiles, id=shooter_id, role="Shooter")

        existing = CoachShooterRelation.objects.filter(coach=coach, shooter=shooter).first()
        if existing:
            return JsonResponse({'success':False, 'warning': 'Already assigned.'})
        CoachShooterRelation.objects.create(coach=coach, shooter=shooter, status="Accepted")
        return JsonResponse({'success': True})
    return JsonResponse({'success':False, 'error': 'Invalid request method.'})

@login_required
def unassign_coach(request, coach_id, shooter_id):
    if request.method == 'POST':
        coach = get_object_or_404(UserProfiles, id=coach_id, role='Coach')
        shooter = get_object_or_404(UserProfiles, id=shooter_id, role='Shooter')      
        relation = CoachShooterRelation.objects.filter(coach=coach, shooter=shooter).first()
        if relation:
            relation.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'No existing relation found to delete.'})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def remove_affiliation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data.get("user_id")
        user_type = data.get("user_type")  # Should be either 'Shooter' or 'Coach'

        try:
            profile = UserProfiles.objects.get(id=user_id)

            # Check that the user_type matches
            if profile.role != user_type:
                messages.error(request, f"The selected user is not a valid {user_type.lower()}.")
                return JsonResponse({"status": "error"}, status=403)

            club_name = profile.affiliated_club if profile.affiliated_club else "your club"
            profile.affiliated_club = None
            profile.save()

            # # Notification message based on type
            # notif_title = "Removed from Club"
            # notif_message = f"You have been removed from {club_name}."

            # Notification.objects.create(
            #     user=profile.user,
            #     title=notif_title,
            #     message=notif_message,
            # )

            messages.success(request, f"{profile.username} ({user_type}) has been removed from the club.")
            return JsonResponse({"status": "success"})

        except UserProfiles.DoesNotExist:
            messages.error(request, f"{user_type} not found.")
            return JsonResponse({"status": "error"}, status=404)

    messages.error(request, "Invalid request method.")
    return JsonResponse({"status": "error"}, status=400)