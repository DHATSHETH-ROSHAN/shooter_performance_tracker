from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home, name = 'home'),
    path('login/', views.user_login, name = 'login'),
    path('logout/', views.user_logout, name='logout'),
    # password reset views 
    path('forgotpassword', views.forgot_password, name='forgot_pass'),
    path('password_rest/', auth_views.PasswordResetView.as_view(
        template_name="pass/password_reset.html"
    ), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(
        template_name="pass/password_reset_done.html"
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
        template_name='pass/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='pass/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('register/', views.user_register, name = 'register'),
    path('activities/', views.user_activities, name='activities'),
    path('shooter/home/', views.shooter_home, name = 'shooter_home'),

    path('coach/home/',views.coach_home, name= 'coach_home'),
    
    path('login/home/', views.user_admin, name = 'admin_home'),
   
]
