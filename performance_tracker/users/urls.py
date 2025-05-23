from django.contrib.auth import views as auth_views
from django.urls import path
from message.views import chat_view
from . import views

urlpatterns = [
    path('',views.home, name = 'home'),
    path('login/', views.user_login, name = 'login'),
    path('logout/', views.user_logout, name='logout'),
    # registration url
    path('register/', views.user_register, name = 'register'),
    # role based reroutingS 
    path('shooter/home/', views.shooter_home, name = 'shooter_home'),
    path('coach/home/',views.coach_home, name= 'coach_home'),


    # password reset views 
    path('forgotpassword', views.forgot_password, name='forgot_pass'),
    path('password_rest/', auth_views.PasswordResetView.as_view(template_name="pass/password_reset.html"), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name="pass/password_reset_done.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='pass/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='pass/password_reset_complete.html'), name='password_reset_complete'),

    # admins staff approval links 
    path("admin/approve_staff/<int:user_id>/", views.approve_staff, name="approve_staff"),
    path("admin/reject_staff/<int:user_id>/", views.reject_staff, name="reject_staff"),

    path('selection/', views.select_coach_or_shooter, name='select_coach_or_shooter'),
    path('accept-request/<int:request_id>/', views.accept_request, name='accept_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),
    path('remove_shooter/<int:shooter_id>/', views.remove_shooter, name='remove_shooter'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('update_max_shooters/', views.update_max_shooters, name='update_max_shooters'),
    path("delete_account/", views.delete_account, name="delete_account"),
    path('remove-coach/', views.remove_coach, name='remove_coach'), 
    

    path('message/chat/<int:user_id>/', chat_view, name='chat_view'),
    path('chat/load/<int:user_id>/', views.load_chat, name='load_chat'),
]
