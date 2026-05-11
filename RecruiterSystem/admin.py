from django.contrib import admin
from .models import User, Event, Registration

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'role', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username']
    list_filter = ['role', 'is_staff', 'is_superuser']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_name', 'city', 'state', 'event_datetime', 'capacity']
    list_filter = ['city', 'state']
    search_fields = ['event_name']

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['recruiter', 'event', 'status', 'registration_datetime']
    list_filter = ['status']