from typing import Any
from django.contrib import admin
from django.http import HttpRequest
from .models import UserProfiles

@admin.register(UserProfiles)
class UserProfilesAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'created_at', 'password', 'is_staff', 'is_active', 'is_superuser' )  # Customize what you see
    list_editable = ('role','is_staff', 'is_active') # editable directly from admin page
    search_fields = ('username', 'email')  # Enable search bar
    list_filter = ('role','created_at')  # Add filter options
    ordering = ('created_at',) # orders the userr by creation date
    readonly_fields = ('id', 'email', 'created_at')
    def get_readonly_fields(self, request, obj=None):
        if obj: # if editing an exiting user make password readonly
            return self.readonly_fields +('password',)
        return self.readonly_fields
# Register your models here.