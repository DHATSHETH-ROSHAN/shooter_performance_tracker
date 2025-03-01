from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import UserProfiles
from scores.models import Score
from datetime import timedelta

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
            user = authenticate(request, username=email, password = password) # the authenticate function withthe django authenticates the user
            if user is not None:
                login(request, user)
                messages.success(request, 'Login Successful !!')

                if user.role == 'Shooter':
                    return redirect('shooter_home')  # the url name that i used in the urlss.py for the home page of the shooter
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
            messages.success(request, 'Registration successfull!, Please login to continue')
            return redirect('login')
    else:
        return render(request, 'register.html')
    
def user_logout(request):
    if request.user.is_superuser:
        return redirect('/admin/logout/')    
    logout(request)
    request.session.flush()
    messages.success(request,'Logged out, successfully')
    return redirect('home')  # Redirect to home after logout

def forgot_password(request):
    return render(request, 'pass/forgotpassword.html')

def user_activities(request):
    if not request.user.is_authenticated:
        messages.warning(request, "You need to login to acess this page!!")
        return redirect('login')
    return render(request, 'activities.html')   

@login_required(login_url='/login/')
def shooter_home(request):
    user = request.user  # Get the logged-in user
    scores_queryset = Score.objects.filter(user_profile= user).order_by('date', '-current_time')
    total_session_40 = scores_queryset.filter(match_type='40-Shots').count()
    total_session_60 = scores_queryset.filter(match_type='60-Shots').count()
    # Get all practice session dates for the user
    practice_dates = scores_queryset.values_list('date', flat=True).distinct()
    streak_count = 0
    current_streak = 0
    previous_date = None
    
    for date in sorted(practice_dates):
        if previous_date is None:
            current_streak = 1
        else:
            if date - previous_date == timedelta(days=1):
                current_streak += 1
            else:
                break  # Streak is broken
        previous_date = date

    streak_count = current_streak
    scores_list = [score.total for score in scores_queryset if score.total is not None]
    best_score_40 = max([score.total for score in scores_queryset if score.match_type == '40-Shots' and score.total is not None],default=0)
    best_score_60 = max([score.total for score in scores_queryset if score.match_type == '60-Shots' and score.total is not None], default=0)
    score_40 = [score.total for score in scores_queryset if score.match_type == '40-Shots' and score.total is not None]
    avg_score_40 = round(sum(score_40) / len(score_40), 2) if score_40 else 0  # Limit avg_score to 2 decimal places
    score_60 = [score.total for score in scores_queryset if score.match_type == '60-Shots' and score.total is not None]
    avg_score_60 = round(sum(score_60)/len(score_60),2) if score_60 else 0
    current_score_40 = score_40[-1] if score_40 else 0  # Last entry for 40-Shots
    current_score_60 = score_60[-1] if score_60 else 0  # Last entry for 60-Shot
    last_session_entry = scores_queryset.first()  # Get the most recent entry
    last_match_type = last_session_entry.match_type if last_session_entry else "40-shots"
    if last_session_entry:  # Check if an entry exists
        last_session = last_session_entry.date  # Retrieve the session date
        session_timing = last_session_entry.duration  # Retrieve the session duration
    else:
        last_session = "No sessions"  # Default value if no session exists
        session_timing = "N/A"  # Default value if no session exists
    target_score_40 = 400
    target_score_60 = 600   
    context = {
        'total_session_40' : total_session_40,
        'total_session_60' : total_session_60,
        'best_score_40' : best_score_40,
        'best_score_60' : best_score_60,
        'current_score_40' : current_score_40,
        'target_score_40' : target_score_40,
        'current_score_60' : current_score_60,
        'target_score_60' : target_score_60,
        'avg_score_40' : avg_score_40,
        'avg_score_60' : avg_score_60,
        'last_session' : last_session,
        'last_match_type' : last_match_type,
        'session_timing' : session_timing,
        'streak_count' : streak_count
    }
    return render(request, 'shooter_home.html', context)

@login_required
def coach_home(request):
    return render(request,'coach_home.html')

def user_admin(request):
    return render(request, 'home.html')
# Create your views here.