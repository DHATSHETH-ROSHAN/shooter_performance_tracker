from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Q, Avg, Max
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
#models import
from .models import UserProfiles, CoachShooterRelation, DayPlanner, Event
from scores.models import manualscore, pdfScore, activities
from message.models import Message
from datetime import timedelta
from django.utils.timezone import now
# importing forms
from .forms import DayPlannerForm, EventForm
# importing other views
from admins.views import *
#importing other needed things
from collections import defaultdict
from decimal import Decimal
from itertools import chain
#imorting json
import json 


def home(request):
    print("User Authenticated:",request.user.is_authenticated)
    if request.user.is_authenticated:
        print("logged in user:" , request.user.first_name)
        print("role:", request.user.role)
        if request.user.role == 'Shooter':
            return redirect('shooter_home')  # the url name that i used in the urlss.py for the home page of the shooter
        elif request.user.role == 'Coach':
            return redirect('coach_home')
        elif request.user.role == 'Staff':
            return redirect('staff_home')
    # if the admin logged in then the home page would be changed automatically
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/admin/')
    return render(request, 'home.html') 

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email','')
        password = request.POST.get('password','')
        try:
            user = authenticate(request, username=email, password=password)  # Fixed spacing
            if user is not None:
                login(request, user)
                messages.success(request, 'Login Successful !!')

                if user.role == 'Shooter':
                    return redirect('shooter_home')
                elif user.role == 'Coach':
                    if user.is_staff == True:
                        print(user.role, user.is_staff, user.is_active, user.is_superuser, user.permitted)
                        return redirect('coach_home')
                    else:
                        messages.error(request, 'Wait till your account get activted')
                        return redirect('home')
                elif user.role == 'Staff':
                    if user.permitted == "Yes":
                        return redirect('staff_home')
                    else:
                        messages.error(request, 'Wait your organization is under approval')
                        return redirect('home')
            else:
                messages.error(request, 'Invalid password!')
                return render(request, 'login.html')
        except UserProfiles.DoesNotExist:
            messages.error(request, 'Invalid credentials! If not registered, please register first.')
            return render(request, 'login.html')
    else:
        return render(request, 'login.html')

def user_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        date_of_birth = request.POST.get('dob')
        mobile_number = request.POST.get('mobile')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'Shooter')
        gender = request.POST.get('gender')
        coaching_specialization = request.POST.get('specialization') if role == "Coach" else None
        years_of_experience = request.POST.get('experience') if role == "Coach" else None
        affiliated_club = request.POST.get('affilated_club')
        if role == "Coach":
            is_staff = True
            is_superuser = False
            is_active = False  # Coach requires admin approval
        elif role == "Admin":
            is_staff = True
            is_superuser = True
            is_active = True
        else:
            is_staff = False
            is_superuser = False
            is_active = True  # Shooter is active immediately

        if not all([first_name, last_name, username, email, password1, password2]):  # Added validation for required fields
            messages.error(request, 'All fields are required!')
            return render(request, 'register.html')
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'register.html')
        elif UserProfiles.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'register.html')
        elif UserProfiles.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return render(request, 'register.html')
        else:
            hashed_pwd = make_password(password1)
            user = UserProfiles.objects.create(first_name=first_name, 
                                               last_name=last_name, 
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
        if role == "Coach":
            messages.success(request, 'Registration successful! Your account is pending approval.')
            return redirect('coach_home')
        elif role == "Staff":
            admin_email = settings.ADMIN_EMAIL
            subject = "New Staff registratoin form the Organization"
            message = f"""
                        A new organization staff has registered and requires approval.
                        Details:
                        Name: {first_name} {last_name}
                        Email: {email}
                        mobile: {mobile_number}
                        Affiliated club: {affiliated_club}
                    Approve or Reject in the admin panel: {request.build_absolute_uri('/admin/users/userprofiles/')}
                    """
            send_mail(subject, message, settings.EMAIL_HOST_USER, [admin_email])
            return redirect('staff_home')
        else:
            messages.success(request, 'Registration successful! Please login to continue.')
            return redirect('login')
    else:
        return render(request, 'register.html')

@login_required
def user_logout(request):
    if not request.user.is_authenticated:  # Added check for authenticated user
        return redirect('home')
    if request.user.is_superuser:
        return redirect('/admin/logout/')    
    logout(request)
    request.session.flush()
    messages.success(request,'Logged out successfully')  
    return redirect('home')

def forgot_password(request):
    return render(request, 'pass/forgotpassword.html') 

def approve_staff(request, user_id):
    user = get_object_or_404(UserProfiles, id=user_id)
    if user.role == "Staff" and user.permitted == "No":
        user.permitted = "Yes" 
        user.is_active = True
        user.save()
        messages.success(request, f"{user.username} has been approved as Staff.")
    return redirect(reverse("admin:users_userprofiles_changelist"))

def reject_staff(request, user_id):
    """"Admin function to reject staff."""
    user = get_object_or_404(UserProfiles, id=user_id)
    if user.role == "Staff" and user.permitted == "No":
        user.is_active = False
        user.save()
        messages.warning(request, f"{user.username} hass been rejected.")
    return redirect(reverse("admin:users_userprofiles_changelist"))

@login_required(login_url='/login/')
def shooter_home(request):
    if request.user.role == "Shooter":
        user = request.user
        scores_queryset = manualscore.objects.filter(user_profile=user).order_by('-date', '-current_time')
        scores_Est = pdfScore.objects.filter(user_profile=user).order_by('-date', '-current_time')
        total_session_40 = scores_queryset.filter(match_type='40-Shots').count()
        total_session_60 = scores_queryset.filter(match_type='60-Shots').count()
        tot_ses_40_est = scores_Est.filter(match_type = '40-Shots').count()
        tot_ses_60_est = scores_Est.filter(match_type = "60-Shots").count()
        today = now().date()  # Define 'today' using django.utils.timezone
        age = today.year - user.date_of_birth.year - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        overall_sessions = total_session_40 + total_session_60 + tot_ses_40_est + tot_ses_60_est
        # Streak Calculation
        practice_dates_man = scores_queryset.values_list('date', flat=True).distinct()
        practice_dates_est = scores_Est.values_list('date', flat=True).distinct()
        practice_dates = sorted(set(practice_dates_man) | set(practice_dates_est), reverse=True)  
        practice_days = [date.strftime("%Y-%m-%d") for date in practice_dates]
        activities_lst = activities.objects.filter(user = user).order_by('-date')
        workoutdays = activities_lst.filter(activity_category = "physical").values_list('date', flat=True)
        workoutdays = [date.strftime("%Y-%m-%d") for date in workoutdays]
        meditdays = activities_lst.filter(activity_category = "mental").values_list('date', flat=True)
        meditdays = [date.strftime("%Y-%m-%d") for date in meditdays]
        equipmaindays = activities_lst.filter(activity_category = "equipment").values_list('date', flat=True)
        equipmaindays = [date.strftime("%Y-%m-%d") for date in equipmaindays]
        streak_count = 0
        current_streak = 0
        previous_date = None
        today = now().date()
        current_year = today.year
        current_month = today.month

        for date in sorted(practice_dates_man, reverse=True):
            if previous_date is None or previous_date - date == timedelta(days=1):
                current_streak += 1
            else:
                break
            previous_date = date
        streak_count = current_streak

        # Score Calculations
        scores_list = [score.total for score in scores_queryset if score.total is not None]
        best_score_40 = max([score.total for score in scores_queryset if score.match_type == '40-Shots' and score.total is not None], default=0)
        best_score_60 = max([score.total for score in scores_queryset if score.match_type == '60-Shots' and score.total is not None], default=0)
        score_40 = [score.total for score in scores_queryset if score.match_type == '40-Shots' and score.total is not None]
        avg_score_40 = round(sum(score_40) / len(score_40), 2) if score_40 else 0
        score_60 = [score.total for score in scores_queryset if score.match_type == '60-Shots' and score.total is not None]
        avg_score_60 = round(sum(score_60) / len(score_60), 2) if score_60 else 0
        best_pdf_60_shots = max([score.total for score in scores_Est.filter(match_type="60-Shots") if score.total is not None],default=0)
        
        current_score_40 = score_40[-1] if score_40 else 0
        current_score_60 = score_60[-1] if score_60 else 0
        avg_dur_sun = round(sum(d := [s.duration for s in scores_queryset if s.day == "Sunday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Sunday"]) else 0
        avg_dur_mon = round(sum(d := [s.duration for s in scores_queryset if s.day == "Monday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Monday"]) else 0
        avg_dur_tue = round(sum(d := [s.duration for s in scores_queryset if s.day == "Tuesday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Tuesday"]) else 0
        avg_dur_wed = round(sum(d := [s.duration for s in scores_queryset if s.day == "Wednesday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Wednesday"]) else 0
        avg_dur_thu = round(sum(d := [s.duration for s in scores_queryset if s.day == "Thursday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Thursday"]) else 0
        avg_dur_fri = round(sum(d := [s.duration for s in scores_queryset if s.day == "Friday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Friday"]) else 0
        avg_dur_sat = round(sum(d := [s.duration for s in scores_queryset if s.day == "Saturday"]) / len(d), 1) if (d := [s.duration for s in scores_queryset if s.day == "Saturday"]) else 0
        # Last Session Info
        last_session_entry = scores_queryset.first()
        last_match_type = last_session_entry.match_type if last_session_entry else "40-Shots"

        if last_session_entry:
            last_session = last_session_entry.date
            session_timing = last_session_entry.duration
        else:
            last_session = "No sessions"
            session_timing = "N/A"

        target_score_40 = 400
        target_score_60 = 600
        # coahes
        available_coaches = UserProfiles.objects.filter(role="Coach")
        coach_relation = CoachShooterRelation.objects.filter(shooter=request.user, status="Accepted").first()
        if coach_relation:
            coach_name = coach_relation.coach.id
            current_shooters_count = CoachShooterRelation.objects.filter(coach=coach_name, status="Accepted").count()
        else:
            coach_name = None
            current_shooters_count = 0
        shooter = request.user  # Get the logged-in coach
        # Get all unique conversations where the coach is involved
        messages = Message.objects.filter(Q(sender=shooter) | Q(receiver=shooter)).order_by('-timestamp')
        # Create a conversation list with the last message
        conversations = {}
        for msg in messages:
            other_user = msg.receiver if msg.sender == shooter else msg.sender
            convo_id = f"{shooter.id}_{other_user.id}" if shooter.id < other_user.id else f"{other_user.id}_{shooter.id}"
            
            if convo_id not in conversations:
                conversations[convo_id] = {
                    "other_user": other_user,
                    "last_message": msg,
                    "unread_count": Message.objects.filter(receiver=shooter, sender=other_user, is_read=False).count()
                }
        events = Event.objects.filter(visibility__in=['shooter', 'both'], date__gte=now().date()).order_by('date')
        day_plans = DayPlanner.objects.filter(shooter=request.user, shared_with_shooter=True, date__gte=now().date())
        context = {
            "conversations": conversations.values(),
            'total_session_40': total_session_40,
            'total_session_60': total_session_60,
            'overallsessions': overall_sessions,
            'best_score_40': best_score_40,
            'best_score_60': best_score_60,
            'best_pdf_60_shots' : best_pdf_60_shots,
            'age':age,
            'current_score_40': current_score_40,
            'target_score_40': target_score_40,
            'current_score_60': current_score_60,
            'target_score_60': target_score_60,
            'avg_score_40': avg_score_40,
            'avg_score_60': avg_score_60,
            'avg_dur_sun': avg_dur_sun,
            'avg_dur_mon': avg_dur_mon,
            'avg_dur_tue': avg_dur_tue,
            'avg_dur_wed': avg_dur_wed,
            'avg_dur_thu': avg_dur_thu,
            'avg_dur_fri': avg_dur_fri,
            'avg_dur_sat': avg_dur_sat,
            'last_session': last_session,
            'last_match_type': last_match_type,
            'session_timing': session_timing,
            'streak_count': streak_count,
            'current_year': current_year,
            'current_month': current_month,
            'practice_dates': practice_dates_man,
            'practice_days': json.dumps(practice_days),
            'workoutdates': json.dumps(workoutdays),
            'medidates': json.dumps(meditdays),
            'equipmaindays': json.dumps(equipmaindays),
            'coaches': available_coaches,
            'coach_relation':coach_relation,
            'current_shooters_count' : current_shooters_count,
            'events': events,
            'day_plans': day_plans,
            
        }
        
        return render(request, 'shooter_home.html', context)
    else:
        messages.error(request, 'Your ID is under approval')
        return render(request, 'home')

@login_required
def select_coach_or_shooter(request):
    user_profile = request.user
    if user_profile.role == "Shooter":
        available_coaches = UserProfiles.objects.filter(role="Coach")
        if request.method == "POST":
            coach_id = request.POST.get("coach_id")
            coach_profile = UserProfiles.objects.get(id=coach_id)
            # check if requestsent and rejected
            existing_request = CoachShooterRelation.objects.filter(coach=coach_profile, shooter=user_profile).first()
            if existing_request:
                if existing_request.status == "Rejected":
                    existing_request.status = "Pending"
                    existing_request.save()
                    messages.success(request, "Coaching request sent again!")
                else:
                    messages.warning(request, "request already sent!")
            else:
                CoachShooterRelation.objects.create(coach=coach_profile, shooter=user_profile, status="Pending")
                messages.success(request, "Coaching request sent!")
            return redirect("shooter_home")
        
        return render(request, "shooter_home.html", {"coaches": available_coaches})
    
    elif user_profile.role == "Coach":
        available_shooters = UserProfiles.objects.filter(role="Shooter")  # Fixed typo
        if request.method == "POST":
            shooter_id = request.POST.get("shooter_id")
            shooter_profile = UserProfiles.objects.get(id=shooter_id)
            # Check if a request exists
            existing_request = CoachShooterRelation.objects.filter(coach=user_profile, shooter=shooter_profile).first()
            if existing_request:
                if existing_request.status == "Rejected":
                    existing_request.status = "Pending"  # Reset status for re-request
                    existing_request.save()
                    messages.success(request, "Shooter request sent again!")
                else:
                    messages.warning(request, "Request already sent or accepted!")
            else:
                CoachShooterRelation.objects.create(coach=user_profile, shooter=shooter_profile, status="Pending")
                messages.success(request, "Shooter request sent!")
            return redirect("coach_home")
        return render(request, "select_shooter.html", {"shooters": available_shooters})

@login_required
def update_profile(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        mobile_number = request.POST.get("mobile_number")
        dob = request.POST.get("dob")
        specialization = request.POST.get("specialization")
        experience = request.POST.get("experience")
        gender = request.POST.get("gender")
        affilated = request.POST.get("club")
        userdetails = UserProfiles.objects.get(username=request.user)
        current_club = userdetails.affiliated_club
        category = request.POST.get("category")
        user_profile = UserProfiles.objects.get(username=request.user)
        user_profile.username = name
        user_profile.email = email
        user_profile.date_of_birth = dob
        user_profile.mobile_number = mobile_number
        user_profile.gender = gender
        user_profile.coaching_specialization = specialization
        user_profile.years_of_experience = experience
        user_profile.affiliated_club = affilated
        user_profile.category = category
        if current_club != affilated :
            try:
                club_staff = UserProfiles.objects.filter(affiliated_club=affilated, role='Staff').first()
                old_staff = UserProfiles.objects.filter(affiliated_club=current_club, role='Staff').first()
                Message.objects.filter(sender=old_staff, receiver= request.user).delete()
                if club_staff:
                    Message.objects.create(sender=club_staff, receiver=request.user, content=f"Welcome to {affilated}! We're glad to have you here.")
                
            except Exception as e:
                print(e)
                print("Error while sending message")

        user_profile.save()
        messages.success(request, "Profile updated successfully!")
        # Get the previous page URL (where the request came from)
        previous_page = request.META.get('HTTP_REFERER')
        # Ensure a valid redirect (fallback to shooter_home or coach_home)
        if previous_page:
            return redirect(previous_page)
        elif request.user.is_coach:  # Assuming you have a way to check coach role
            return redirect('coach_home')
        else:
            return redirect('shooter_home')
    else:
        messages.warning(request, 'Your updation request Failed, try again later!!') 
        return redirect('shooter_home')

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user  # Get the logged-in user
        user_profile = UserProfiles.objects.get(username=user)  # Get the user's profile

        # Delete user and logout
        user_profile.delete()
        user.delete()
        logout(request)
        messages.success(request, "Your account has been deleted successfully.")
        return redirect("home")  # Redirect to the home page or login page
    else:
        messages.warning(request, 'Your account has not been deleted, try again later!!')
        return redirect("coach_home")  # If not POST request, redirect to profile

@login_required
def update_max_shooters(request):
    if request.method == "POST":
        max_shooters = request.POST.get("max_shooters")
        if max_shooters and max_shooters.isdigit():
            max_shooters = int(max_shooters)
            if max_shooters < 1 or max_shooters > 100:  # Adjust limits as needed
                messages.error(request, "Invalid number of shooters.")
                return redirect(request.META.get('HTTP_REFERER', 'coach_home'))
            # Update max_shooters for all entries related to the logged-in coach
            updated_count = CoachShooterRelation.objects.filter(coach=request.user).update(max_shooters=max_shooters)
            if updated_count > 0:
                messages.success(request, "Max Shooters updated successfully!")
            else:
                messages.error(request, "No coach profile found.")
        else:
            messages.error(request, "Please enter a valid number.")
    return redirect(request.META.get('HTTP_REFERER', 'coach_home'))

@login_required
def accept_request(request, request_id):
    coach_profile = request.user  # Get the coach's UserProfiles object
    coach_request = get_object_or_404(CoachShooterRelation, id=request_id, coach=coach_profile)
    if coach_request.status != 'Accepted':
        coach_request.status = 'Accepted'
        coach_request.save()
        # Assign the shooter to the coach
        shooter_profile = UserProfiles.objects.get(username=coach_request.shooter)
        shooter_profile.coach = coach_profile  # Assign coach properly
        shooter_profile.save()

        Message.objects.create(sender=coach_profile, receiver=shooter_profile, content="Welcome!, You are now connected for training. Let's start practicing.")
        messages.success(request, "You have accepted the coaching request.")
    return redirect('coach_home')

@login_required
def reject_request(request, request_id):
    coach_request = get_object_or_404(CoachShooterRelation, id=request_id, coach=request.user)
    coach_request.status = 'Rejected'
    coach_request.save()
    messages.warning(request, "You have rejected the coaching request.")
    return redirect('coach_home')

@login_required
def remove_coach(request):
    if request.method == "POST":
        shooter = UserProfiles.objects.get(username=request.user)  
        if shooter.coach:  # Check if a coach is assigned
            coach_profile = shooter.coach
            coach_name = shooter.coach.username  # Store coach's name before unassigning
            shooter.coach = None  # Unassign coach
            shooter.save()
            # Delete the coach-shooter relationship
            CoachShooterRelation.objects.filter(shooter_id=shooter.id).delete()
            # Delete chat history between coach and shooter
            conversation_id = "_".join(sorted([str(shooter.id), str(coach_profile.id)]))
            Message.objects.filter(conversation_id=conversation_id).delete()
            # Show success message
            messages.warning(request, f"You removed {coach_name} as your coach.")
    return redirect('shooter_home')

@login_required
def remove_shooter(request, shooter_id):
    if request.method == "POST":
        coach = UserProfiles.objects.get(username=request.user)  
        shooter = UserProfiles.objects.get(id=shooter_id)  
        if shooter.coach == coach:  # Check if the shooter is assigned to the coach
            shooter_name = shooter.username  
            shooter.coach = None  
            shooter.save()
            CoachShooterRelation.objects.filter(coach_id=coach.id, shooter_id=shooter.id).delete()
            # Delete chat history between coach and shooter
            conversation_id = "_".join(sorted([str(shooter.id), str(coach.id)]))
            Message.objects.filter(conversation_id=conversation_id).delete()
            messages.warning(request, f"You removed {shooter_name} from your shooters list.")
    
    return redirect('coach_home')

@login_required(login_url='/login/')  # Added login_url parameter for consistency
def coach_home(request):
    activecoach = request.user.is_active
    if activecoach == True:
        coach_profile = UserProfiles.objects.get(username=request.user)
        fullprofile = UserProfiles.objects.filter(username=coach_profile).values()
        profile_n = UserProfiles.objects.get(username = coach_profile)
        coach_email = fullprofile[0]['email'] if fullprofile else None
        coach_phone = fullprofile[0]['mobile_number'] if fullprofile else None
        undob = profile_n.date_of_birth
        dob = profile_n.date_of_birth.strftime('%d-%m-%Y') if profile_n.date_of_birth else "NOt Provided"
        gender = fullprofile[0]['gender'] if fullprofile else "Not provided"
        specialization = fullprofile[0]['coaching_specialization'] if fullprofile else None
        experience = fullprofile[0]['years_of_experience'] if fullprofile else None
        club = fullprofile[0]['affiliated_club'] if fullprofile else None
        current_shooters_count = CoachShooterRelation.objects.filter(coach=coach_profile, status="Accepted").count()
        male_shooters_count = CoachShooterRelation.objects.filter(coach=coach_profile, status="Accepted", shooter__gender="Male").count() 
        female_shooters_count = CoachShooterRelation.objects.filter(coach=coach_profile, status="Accepted", shooter__gender="Female").count()
        
        # Retrieve shooters assigned to the coach
        shooters = CoachShooterRelation.objects.filter(coach=coach_profile, status="Accepted").select_related('shooter')
        # Prepare shooter data for the frontend
        shooter_list = []
        hg_40_man_avg = 0
        hg_60_man_avg = 0
        hg_40_est_avg =0
        hg_60_est_avg = 0
        best_shooter_40_man_avg = None
        best_shooter_60_man_avg = None
        best_shooter_40_est_avg = None
        best_shooter_60_est_avg = None
        manual_40_shot_trends = defaultdict(list)
        manual_60_shot_trends = defaultdict(list)
        est_40_shot_trends = defaultdict(list)
        est_60_shot_trends = defaultdict(list)

        hg_40_man = 0
        best_shooter_40_man = None
        hg_60_man = 0
        best_shooter_60_man = None
        hg_40_est = 0
        best_shooter_40_est = None
        hg_60_est = 0
        best_shooter_60_est = None
        recent_scores_man = (manualscore.objects.order_by('user_profile', '-date').distinct('user_profile').values('user_profile__username', 'total', 'date', 'match_type'))
        recent_scores_est = (pdfScore.objects.order_by('user_profile', '-date').distinct('user_profile').values('user_profile__username', 'total', 'date', 'match_type'))
        for score in recent_scores_man:
            score['type'] = 'Manual'  # Mark manual scores
        for score in recent_scores_est:
            score['type'] = 'EST'  # Mark EST scores
        # Merge the two lists
        combined_scores = list(chain(recent_scores_man, recent_scores_est))
        # Sort the merged list by date (most recent first)
        combined_scores = sorted(combined_scores, key=lambda x: x['date'], reverse=True)
        for relation in shooters:
            shooter = relation.shooter
            shooter_id = shooter.id
            # Calculate averages for 40-shot and 60-shot matches (Manual Scores)
            manual_40_avg = round(manualscore.objects.filter(user_profile_id=shooter_id, match_type="40-Shots").aggregate(avg_score=Avg('total'))['avg_score'] or 0, 1)
            manual_60_avg = round(manualscore.objects.filter(user_profile_id=shooter_id, match_type="60-Shots").aggregate(avg_score=Avg('total'))['avg_score'] or 0, 1)
            # Calculate averages for 40-shot and 60-shot matches (PDF Scores)
            pdf_40_avg = round(pdfScore.objects.filter(user_profile_id=shooter_id, match_type="40-Shots").aggregate(avg_score=Avg('total'))['avg_score'] or 0, 1)
            pdf_60_avg = round(pdfScore.objects.filter(user_profile_id=shooter_id, match_type="60-Shots").aggregate(avg_score=Avg('total'))['avg_score'] or 0, 1)
            # Calculate highest scores for 40-shot and 60-shot matches (Manual Scores)
            manual_40_high = manualscore.objects.filter(user_profile_id=shooter_id, match_type="40-Shots").aggregate(high_score=Max('total'))['high_score'] or 0
            manual_60_high = manualscore.objects.filter(user_profile_id=shooter_id, match_type="60-Shots").aggregate(high_score=Max('total'))['high_score'] or 0
            # calculate the scrores of shooters individually
            manual_scores_40 = manualscore.objects.filter(user_profile_id=shooter_id, match_type="40-Shots").values("date", "total").order_by("date")
            manual_scores_60 = manualscore.objects.filter(user_profile_id=shooter_id, match_type="60-Shots").values("date", "total").order_by("date")
            est_scores_40 = pdfScore.objects.filter(user_profile_id= shooter_id, match_type="40-Shots").values("date", "total").order_by("date")
            est_scores_60 = pdfScore.objects.filter(user_profile_id=shooter_id, match_type="60-Shots").values("date", "total").order_by("date")
            # Store data separately
            manual_40_shot_trends[shooter.username] = [{"date": entry["date"].strftime("%Y-%m-%d"), "score": entry["total"]} for entry in manual_scores_40 if entry["date"]]
            manual_60_shot_trends[shooter.username] = [{"date": entry["date"].strftime("%Y-%m-%d"), "score": entry["total"]} for entry in manual_scores_60 if entry["date"]]
            est_40_shot_trends[shooter.username] = [{"date": entry["date"].strftime("%Y-%m-%d"), "score": entry["total"]} for entry in est_scores_40 if entry["date"]]
            est_60_shot_trends[shooter.username] = [{"date": entry["date"].strftime("%Y-%m-%d"), "score": entry["total"]} for entry in est_scores_60 if entry["date"]] 
            # Calculate highest scores for 40-shot and 60-shot matches (PDF Scores)
            pdf_40_high = pdfScore.objects.filter(user_profile_id=shooter_id, match_type="40-Shots").aggregate(high_score=Max('total'))['high_score'] or 0
            pdf_60_high = pdfScore.objects.filter(user_profile_id=shooter_id, match_type="60-Shots").aggregate(high_score=Max('total'))['high_score'] or 0
            #for 40 shots man
            if manual_40_avg > hg_40_man_avg:
                hg_40_man_avg = manual_40_avg
                best_shooter_40_man_avg = shooter.username
            # for 60 shots man
            if manual_60_avg > hg_60_man_avg:
                hg_60_man_avg = manual_60_avg
                best_shooter_60_man_avg = shooter.username
            # for est 40 shots
            if pdf_40_avg > hg_40_est_avg:
                hg_40_est_avg = pdf_40_avg
                best_shooter_40_est_avg = shooter.username
            # for est 60 shots
            if pdf_60_avg > hg_60_est_avg:
                hg_60_est_avg = pdf_60_avg
                best_shooter_60_est_avg = shooter.username
            # for high scores 
            if manual_40_high > hg_40_man:
                hg_40_man = manual_40_high
                best_shooter_40_man = shooter.username

            if manual_60_high > hg_60_man:
                hg_60_man = manual_60_high
                best_shooter_60_man = shooter.username

            if pdf_40_high > hg_40_est:
                hg_40_est= pdf_40_high
                best_shooter_40_est = shooter.username

            if pdf_60_high > hg_60_est:
                hg_60_est = pdf_60_high
                best_shooter_60_est = shooter.username
                
            shooter_list.append({
                "id": shooter.id,
                "name": shooter.username,
                "man_40_avg": manual_40_avg,
                "man_60_avg": manual_60_avg,
                "est_40_avg": pdf_40_avg,
                "est_60_avg": pdf_60_avg
                # "average_score": shooter.average,  # Ensure this field exists in the model
            })
        pending_requests = CoachShooterRelation.objects.filter(coach=coach_profile, status="Pending")
        count_pending_req = pending_requests.count()
    # max_shooters = CoachShooterRelation.objects.filter(coach=coach_profile).first().max_shooters if CoachShooterRelation.objects.filter(coach=coach_profile).exists() else "N/A"
        relation = CoachShooterRelation.objects.filter(coach=coach_profile).first()
        max_shooters = relation.max_shooters if relation else "N/A"
        # Day planner handling
        # Filter out expired day plans (only keep today's and future plans)
        day_plans = DayPlanner.objects.filter(coach=request.user, date__gte=now().date())
        form1 = DayPlannerForm(coach=request.user)
        form2 = EventForm()
        # Retrieve recent activities of all shooters trained under this coach
    # recent_activities = activities.objects.filter(user__in=[shooter['id'] for shooter in shooter_list]).order_by('-date')[:10]
        
        shooter_ids = [relation.shooter.id for relation in shooters]
        recent_activities = activities.objects.filter(user_id__in=shooter_ids).order_by('-date')[:10]

        if request.method == "POST":
            if "day_planner_submit" in request.POST:
                form1 = DayPlannerForm(request.POST, coach=request.user)
                if form1.is_valid():
                    plan = form1.save(commit=False)
                    plan.coach = request.user
                    plan.save()
                    return redirect("coach_home")  # Reload the page
            
            elif "event_submit" in request.POST:
                form2 = EventForm(request.POST)
                if form2.is_valid():
                    event = form2.save(commit=False)
                    event.created_by = request.user
                    event.save()
                    form2.save_m2m()  # Save assigned shooters
                    return redirect('coach_home')

        # Filter out expired events (only keep today's and future events)
        events = Event.objects.filter(visibility__in=['coach', 'both'], date__gte=now().date()).order_by('date')
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError
        # messagess thing
        coach = request.user  # Get the logged-in coach
        # Get all unique conversations where the coach is involved
        messages = Message.objects.filter(Q(sender=coach) | Q(receiver=coach)).order_by('-timestamp')
        # Create a conversation list with the last message
        conversations = {}
        for msg in messages:
            other_user = msg.receiver if msg.sender == coach else msg.sender
            convo_id = f"{coach.id}_{other_user.id}" if coach.id < other_user.id else f"{other_user.id}_{coach.id}"
            
            if convo_id not in conversations:
                conversations[convo_id] = {
                    "other_user": other_user,
                    "last_message": msg,
                    "unread_count": Message.objects.filter(receiver=coach, sender=other_user, is_read=False).count()
                }

        context = {
            'coach_name': coach_profile,
            'coach_email': coach_email,
            'coach_phone': coach_phone,
            'date_of_birth': dob,
            'dob': undob,
            'specialization': specialization,
            'experience': experience,
            'club': club,
            'gender': gender,
            "pending_requests": pending_requests,  # Your existing logic
            "conversations": conversations.values(),
            'max_shooters': max_shooters,
            'shooters_count':current_shooters_count,
            'male_shooters_count': male_shooters_count,
            'female_shooters_count': female_shooters_count,
            'pending_requests': pending_requests,
            "pending_requests_count": count_pending_req,
            'shooters': shooter_list,
            'day_plans': day_plans,

            'events': events, 
            'form1': form1,
            'form2': form2,
            #highest averages
            'hg_40_man_avg':hg_40_man_avg,
            'hg_60_man_avg':hg_60_man_avg,
            'hg_40_est_avg':hg_40_est_avg,
            'hg_60_est_avg':hg_60_est_avg,
            # shooter name of highest average
            'best_sh_40_man_avg':best_shooter_40_man_avg,
            'best_sh_60_man_avg':best_shooter_60_man_avg,
            'best_sh_40_est_avg':best_shooter_40_est_avg,
            'best_sh_60_est_avg':best_shooter_60_est_avg,
            # highest scores
            'hg_40_man':hg_40_man,
            'hg_60_man':hg_60_man,
            'hg_40_est':hg_40_est,
            'hg_60_est':hg_60_est,
            #high scorer names
            'best_sh_40_man':best_shooter_40_man,
            'best_sh_60_man':best_shooter_60_man,
            'best_sh_40_est':best_shooter_40_est,
            'best_sh_60_est':best_shooter_60_est,
            'recent_activities': recent_activities,
            "recent_scores": combined_scores,
            "manual_40_shot_trends": json.dumps(manual_40_shot_trends, default=decimal_to_float),
            "manual_60_shot_trends": json.dumps(manual_60_shot_trends, default=decimal_to_float),
            "est_40_shot_trends": json.dumps(est_40_shot_trends, default=decimal_to_float),
            "est_60_shot_trends": json.dumps(est_60_shot_trends, default=decimal_to_float),
        }
        return render(request, 'coach_home.html', context)
    
    else:
        messages.warning(request, "Wait till Admin accepts you as coach")
        return render(request, 'home')


@login_required
def load_chat(request, user_id):
    other_user_profile = UserProfiles.objects.get(id=user_id)
    other_user = other_user_profile
    
    conversation_id = "_".join(sorted([str(request.user.id), str(other_user.id)]))
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    
    print(messages, other_user, conversation_id)
    return render(request, 'message/chat_message.html', {
        'messages': messages,
        'other_user': other_user,
        'conversation_id':conversation_id
    })

@login_required 
def user_admin(request):
    if not request.user.role == 'Admin':  # Added role check for admin
        messages.error(request, 'You do not have permission to access this page')
        return redirect('home')
    return render(request, 'home.html')
