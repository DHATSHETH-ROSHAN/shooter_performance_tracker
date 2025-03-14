from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import UserProfiles
from scores.models import manualscore, pdfScore, activities
from datetime import timedelta
from django.utils.timezone import now
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
        elif request.user.role == 'Admin':
            return redirect('home')
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
                    return redirect('coach_home')
                elif user.role == 'Admin':
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
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'Shooter')

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
            user = UserProfiles.objects.create(first_name=first_name, last_name=last_name, username=username, email=email, password=hashed_pwd, role=role)
            user.save()
            messages.success(request, 'Registration successful!, Please login to continue')  # Fixed typo
            return redirect('login')
    else:
        return render(request, 'register.html')
    
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

@login_required(login_url='/login/')
def shooter_home(request):
    user = request.user
    scores_queryset = manualscore.objects.filter(user_profile=user).order_by('-date', '-current_time')
    scores_Est = pdfScore.objects.filter(user_profile=user).order_by('-date', '-current_time')
    total_session_40 = scores_queryset.filter(match_type='40-Shots').count()
    total_session_60 = scores_queryset.filter(match_type='60-Shots').count()
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

    context = {
        'total_session_40': total_session_40,
        'total_session_60': total_session_60,
        'best_score_40': best_score_40,
        'best_score_60': best_score_60,
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
    }
    
    return render(request, 'shooter_home.html', context)



@login_required  # Added login_url parameter for consistency
def coach_home(request):
    return render(request, 'coach_home.html')

@login_required  # Added login_url parameter for consistency
def user_admin(request):
    if not request.user.role == 'Admin':  # Added role check for admin
        messages.error(request, 'You do not have permission to access this page')
        return redirect('home')
    return render(request, 'home.html')
