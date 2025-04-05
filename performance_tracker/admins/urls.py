from django.contrib.auth import views as auth_views
from django.urls import path
from .views import staff_home, get_coach_details, get_shooter_details, add_new_shooter, add_new_coach, coach_shooter_relation, shooter_coach_relation

urlpatterns = [

path('home/', staff_home, name = 'staff_home'),
path('get-shooter-details/<int:shooter_id>/', get_shooter_details, name='get_shooter_details'),
path('get-coach-details/<int:coach_id>/', get_coach_details, name='get_coach_details'),

path('home/add-shooter/', add_new_shooter, name='add_shooter'),
path('home/add-coach/', add_new_coach, name="add_coach"),

path('coach-shooter-relation/<int:coachId>/', coach_shooter_relation, name='coach_shooter_relation'),
path('shooter-coach-relation/<int:shooterId>/', shooter_coach_relation, name='shooter_coach_relation'),

]