from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, WorkerProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_active']
    list_filter = ['role', 'is_verified', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'avatar', 'is_verified')
        }),
    )

@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience_years', 'hourly_rate', 'rating', 'is_available']
    list_filter = ['is_available', 'experience_years']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['specializations']