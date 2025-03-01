from django.urls import path
from . import views

urlpatterns = [
    path('shooter/home/manual_upload/', views.manual_upload, name='manual_upload'),
    path('shooter/home/pdf_upload', views.pdf_uploading, name='pdf_upload'),
    path('shooter/home/analytics/',views.analytics, name='analytics'),
    path('shooter/home/dashboard', views.dashboard, name='dashboard'),
]