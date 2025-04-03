from django.contrib.auth import views as auth_views
from django.urls import path
from .views import staff_home, get_coach_details, get_shooter_details

urlpatterns = [

path('home/', staff_home, name = 'staff_home'),
path('get-shooter-details/<int:shooter_id>/', get_shooter_details, name='get_shooter_details'),
path('get-coach-details/<int:coach_id>/', get_coach_details, name='get_coach_details'),


]