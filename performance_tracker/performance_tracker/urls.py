from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
    path('', include('users.urls')),
    path('score/', include('scores.urls')),
    path('staff/', include('admins.urls')),
    path('admin/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path("message/", include("message.urls")),
    
]
