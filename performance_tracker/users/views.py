from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages
from .models import UserProfiles

def home(request):
    print("User Authenticated:",request.user.is_authenticated)
    return render(request, 'home.html') 

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email','')
        password = request.POST.get('password','')
        try:
            #user = UserProfiles.objects.get(email=email) # this fetches the userrname using the email
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
    logout(request)
    return redirect('home')  # Redirect to home after logout

def forgot_password(request):
    return render(request, 'pass/forgotpassword.html')

@login_required(login_url='/login/')
def user_activities(request):
    messages.warning(request, "You need to login to acess this page!!")
    return render(request, 'activities.html')   

def shooter_home(request):
    return render(request, 'shooter_home.html')

def coach_home(request):
    return render(request,'coach_home.html')

def user_admin(request):
    return render(request, 'home.html')
# Create your views here.