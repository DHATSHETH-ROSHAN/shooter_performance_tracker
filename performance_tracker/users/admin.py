from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from .models import UserProfiles, DayPlanner, Event, CoachShooterRelation
from scores.models import *

@admin.register(UserProfiles)
class UserProfilesAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'created_at', 'is_staff', 'is_active', 'is_superuser','permitted', 'accept_reject_buttons' )  # Customize what you see
    list_editable = ('role', 'is_active', 'permitted', 'is_superuser') # editable directly from admin page
    list_display_links = ('id','username','email')
    search_fields = ('username', 'email')  # Enable search bar
    list_filter = ('role','created_at')  # Add filter options
    ordering = ('created_at',) # orders the userr by creation date
    readonly_fields = ( 'email', 'created_at')
    actions = ['accept_staff', 'reject_staff']

    def accept_reject_buttons(self, obj):
        if obj.role == 'Staff' and obj.permitted == 'No':
            return format_html('<a class="button" style="color:green;" href="/admin/approve_staff/{}/">Accept</a> &nbsp;' '<a class="button" style="color:red;" href="/admin/reject_staff/{}/">Reject</a>', obj.id , obj.id)
        return "Approved" if obj.permitted == "Yes" else "Not Applicable"
    accept_reject_buttons.short_description = "Actions"
    accept_reject_buttons.allow_tags = True

    def accept_Staff(self, request, queryset):
        # bulk action to chosse approved staff
        queryset.filter(role="Staff", permitted = 'No').update(permitted = 'Yes', is_active= True)
        self.message_user(request, "Selected member has been accepted as staff of organization")

    def reject_staff(self, request, queryset):
        # bulk action to reject the selectted staffs
        queryset.filter(role="Staff", permitted = 'No').upadate(permitted = "No", is_active=False)
        self.message_user(request, 'Selected staff members have been rejected')

    def get_readonly_fields(self, request, obj=None):
        if obj: # if editing an exiting user make password readonly
            return self.readonly_fields + ('password',)
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        """ Ensure changes are properly saved """
        if change:  # If object is being updated
            print(obj) # prints the username where the change applied
            obj.save()
        super().save_model(request, obj, form, change)

@admin.register(DayPlanner)
class DayPlanner(admin.ModelAdmin):
    list_display = ('coach', 'shooter', 'date', 'time', 'activity', 'shared_with_shooter')
    ordering = ('date',)
    list_filter = ( 'shooter', 'date')
@admin.register(Event)
class Event(admin.ModelAdmin):
    list_display = ('title', 'date', 'location', 'description', 'created_by', 'visibility',)
    list_display_links = ('title',)
    list_editable = ( 'date', 'location', 'description', 'created_by', 'visibility',)
    search_fields = ('title', 'location', 'date')
    list_filter = ('title', 'location', 'date')
    filter_horizontal = ('assigned_shooters',)
    ordering = ('date',)

@admin.register(activities)
class activities(admin.ModelAdmin):
    list_display = ('user', 'activity_category', 'activity_name', 'duration', 'notes', 'created_at', 'date',)
    search_fields = ('user',)
    list_filter = ('user','activity_name', 'date')

@admin.register(manualscore)
class manualscore(admin.ModelAdmin):
    list_display = ('get_username', 'match_type', 'series_1','series_2', 'series_3', 'series_4', 'series_5', 'series_6', 'total', 'average', 'notes', 'adjustment_made', 'date', 'day')
    search_fields = ('match_type', 'total', )
    ordering = ('date',)
    list_filter = ('user_profile', 'match_type', 'date')

    def get_username(self, obj):
        if obj.user_profile: 
            return f"{obj.user_profile.first_name} {obj.user_profile.last_name}"
        return "No User"  
    get_username.short_description = "Shooter Name"

@admin.register(pdfScore)
class PdfScore(admin.ModelAdmin):
    list_display = ('get_username', 'match_type', 'series_1', 'series_2', 'series_3', 'series_4', 'series_5', 'series_6', 'total', 'date', 'day', 'current_time', 'adjustment_made')
    search_fields = ( 'get_username','match_type', )
    ordering = ('date',)
    list_filter = ('user_profile', 'match_type', 'date')

    def get_username(self, obj):
        if obj.user_profile: 
            return f"{obj.user_profile.first_name} {obj.user_profile.last_name}"
        return "No User"  
    get_username.short_description = "Shooter Name"

@admin.register(CoachShooterRelation)
class coachshooterrelation(admin.ModelAdmin):
    list_display = ('coach', 'shooter', 'status', 'max_shooters', 'accepting_shooters')
    ordering = ('coach', 'status')
    list_filter = ('coach', 'shooter', 'status',)
# Register your models here.