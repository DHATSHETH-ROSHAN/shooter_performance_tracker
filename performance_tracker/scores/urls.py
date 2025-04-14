from django.urls import path
from . import views

urlpatterns = [
    path('shooter/home/manual_upload/', views.manual_upload, name='manual_upload'),
    path('shooter/home/pdf_upload', views.pdf_uploading, name='pdf_upload'),
    path('shooter/home/analytics/',views.analytics, name='analytics'),
    path('shooter/home/dashboard/', views.dashboard, name='dashboard'),
    path('shooter/home/history', views.history, name='history'),
    path('shooter/home/activities/', views.user_activities, name='activities'),
    path('coach/home/inspect/dashboard/<int:id>/', views.inspect, name='inspect'),
    path('get-activity-modal/<int:activity_id>/', views.get_activity_modal, name='get_activity_modal')
]