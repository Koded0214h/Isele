from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
import json
from .models import EventManagerUser, Event
from datetime import datetime, timedelta
import re

# Initialize Twilio client
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages via Twilio"""
    try:
        # Get the incoming message details
        from_number = request.POST.get('From', '')
        message_body = request.POST.get('Body', '').strip().lower()
        
        # Extract phone number (remove 'whatsapp:' prefix)
        phone_number = from_number.replace('whatsapp:', '')
        
        # Get or create user
        user, created = EventManagerUser.objects.get_or_create(phone_number=phone_number)
        
        # Process the message
        response_text = process_message(user, message_body)
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return HttpResponse(str(resp), content_type='text/xml')
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error. Please try again.")
        return HttpResponse(str(resp), content_type='text/xml')

def process_message(user, message):
    """Process the incoming message and return appropriate response"""
    message = message.lower().strip()
    
    # Help/Start command
    if message in ['hi', 'hello', 'hey', 'start', 'help', 'menu']:
        return get_main_menu()
    
    # View upcoming events
    elif any(keyword in message for keyword in ['events', 'upcoming', 'schedule', 'plans']):
        return get_upcoming_events(user)
    
    # View today's events
    elif any(keyword in message for keyword in ['today', "today's", 'agenda']):
        return get_todays_events(user)
    
    # Create event (basic version - we'll enhance with AI later)
    elif any(keyword in message for keyword in ['create', 'add', 'schedule', 'new event', 'set up']):
        return "I see you want to create an event. For now, please use the format: 'Meeting with John tomorrow at 3pm'. I'll add AI parsing soon! 🚀"
    
    # Default response
    else:
        return "I'm your Event Manager bot! 🤖\n\n" + get_main_menu()

def get_main_menu():
    """Return the main menu message"""
    return """📅 *Event Manager Menu* 📅

Here's what I can do:
• *View Events* - See your upcoming events
• *Today's Agenda* - See what's happening today  
• *Create Event* - Schedule a new event (say 'create meeting tomorrow at 2pm')

Just tell me what you'd like to do! 💬"""

def get_upcoming_events(user):
    """Get user's upcoming events"""
    now = timezone.now()
    upcoming_events = Event.objects.filter(
        user=user, 
        scheduled_time__gte=now
    )[:10]  # Limit to 10 events
    
    if not upcoming_events:
        return "You have no upcoming events! 🎉\n\nUse 'create' to schedule something new."
    
    response = "📅 *Your Upcoming Events:*\n\n"
    for event in upcoming_events:
        time_str = event.scheduled_time.strftime('%a, %b %d at %I:%M %p')
        location_str = f" @ {event.location}" if event.location else ""
        response += f"• *{event.title}*\n  {time_str}{location_str}\n\n"
    
    return response

def get_todays_events(user):
    """Get user's events for today"""
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    todays_events = Event.objects.filter(
        user=user,
        scheduled_time__date=today
    ).order_by('scheduled_time')
    
    if not todays_events:
        return "No events scheduled for today! 🕶️\n\nEnjoy your free time!"
    
    response = f"📋 *Today's Agenda ({today.strftime('%A, %b %d')}):*\n\n"
    for event in todays_events:
        time_str = event.scheduled_time.strftime('%I:%M %p')
        location_str = f" @ {event.location}" if event.location else ""
        response += f"• *{time_str}* - {event.title}{location_str}\n"
    
    return response