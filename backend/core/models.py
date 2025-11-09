from django.db import models
from django.utils import timezone

class EventManagerUser(models.Model):
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=10, default='en')
    current_conversation_state = models.JSONField(blank=True, null=True)  # Store temporary conversation data
    
    def __str__(self):
        return f"{self.phone_number} ({self.name})" if self.name else self.phone_number
    
    def clear_conversation_state(self):
        """Clear any temporary conversation state"""
        self.current_conversation_state = None
        self.save()

class Event(models.Model):
    user = models.ForeignKey(EventManagerUser, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    scheduled_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
    
    def is_upcoming(self):
        return self.scheduled_time >= timezone.now()