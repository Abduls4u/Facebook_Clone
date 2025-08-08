from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'is_online', 'created_at']
    list_filter = ['is_online', 'is_verified', 'profile_visibility', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('bio', 'profile_picture', 'cover_photo', 'date_of_birth')
        }),
        ('Personal Details', {
            'fields': ('phone_number', 'website', 'location', 'work', 'education')
        }),
        ('Settings', {
            'fields': ('profile_visibility', 'is_verified', 'is_online')
        }),
    )