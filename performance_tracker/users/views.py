from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import UserProfiles
from scores.models import Score

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
    scores_queryset = Score.objects.filter(user_profile= user).order_by('-date', 'current_time')
    total_sesion = scores_queryset.count()
    scores_list = [score.total for score in scores_queryset if score.total is not None]
    best_score = max(scores_list, default=0)
    avg_score = sum(scores_list) / len(scores_list) if scores_list else 0
    current_score = scores_list[0] if scores_list else 0
    last_session_entry = scores_queryset.first()  # Get the most recent entry
    if last_session_entry:  # Check if an entry exists
        last_session = last_session_entry.date  # Retrieve the session date
        session_timing = last_session_entry.duration  # Retrieve the session duration
    else:
        last_session = "No sessions"  # Default value if no session exists
        session_timing = "N/A"  # Default value if no session exists
    target_score = 400
    context = {
        'total_sesion' : total_sesion,
        'best_score' : best_score,
        'current_score' : current_score,
        'target_score' : target_score,
        'avg_score' : avg_score,
        'last_session' : last_session,
        'session_timing' : session_timing,
    }
    return render(request, 'shooter_home.html', context)

@login_required
def coach_home(request):
    return render(request,'coach_home.html')

def user_admin(request):
    return render(request, 'home.html')
# Create your views here.