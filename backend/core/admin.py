from django.contrib import admin
from .models import EventManagerUser, Event

@admin.register(EventManagerUser)
class EventManagerUserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'created_at']
    search_fields = ['phone_number', 'name']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'scheduled_time', 'location', 'is_recurring']
    list_filter = ['scheduled_time', 'is_recurring']
    search_fields = ['title', 'location']
    date_hierarchy = 'scheduled_time'