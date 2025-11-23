from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os
import json
import logging
from .models import EventManagerUser, Event
from .event_creator import EventCreationService
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

# Initialize Twilio client
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages via Twilio"""
    try:
        # Get the incoming message details
        from_number = request.POST.get('From', '')
        message_body = request.POST.get('Body', '').strip()
        
        print(f"📱 Received message from {from_number}: {message_body}")  # DEBUG
        
        # Extract phone number (remove 'whatsapp:' prefix)
        phone_number = from_number.replace('whatsapp:', '')
        
        # Get or create user
        user, created = EventManagerUser.objects.get_or_create(phone_number=phone_number)
        if created:
            print(f"👤 New user created: {phone_number}")
        
        # Process the message
        response_text = process_message(user, message_body)
        
        # Create TwiML response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return HttpResponse(str(resp), content_type='text/xml')
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error. Please try again.")
        return HttpResponse(str(resp), content_type='text/xml')

def process_message(user, message):
    """Process the incoming message and return appropriate response"""
    message_lower = message.lower().strip()
    
    print(f"🔍 Processing: '{message}' -> '{message_lower}'")  # DEBUG
    
    # Help/Start command
    if message_lower in ['hi', 'hello', 'hey', 'start', 'help', 'menu']:
        print("✅ Triggered: Main menu")  # DEBUG
        return get_main_menu()
    
    # View upcoming events
    elif any(keyword in message_lower for keyword in ['events', 'upcoming', 'schedule', 'plans', 'what do i have']):
        print("✅ Triggered: View events")  # DEBUG
        return get_upcoming_events(user)
    
    # View today's events
    elif any(keyword in message_lower for keyword in ['today', "today's", 'agenda']):
        print("✅ Triggered: Today's agenda")  # DEBUG
        return get_todays_events(user)
    
    # Cancel or clear state
    elif any(keyword in message_lower for keyword in ['cancel', 'clear', 'stop']):
        user.clear_conversation_state()
        return "✅ Conversation cleared. How can I help you?"
    
    # Check if we're in the middle of event creation
    elif user.current_conversation_state and user.current_conversation_state.get('creating_event'):
        print("✅ Triggered: Continue event creation")  # DEBUG
        event_service = EventCreationService(user)
        return event_service.process_event_creation(message)
    
    # 🚨 PERMISSIVE EVENT CREATION DETECTION 🚨
    # If message contains time/date words, assume it's event creation
    time_date_words = [
        'tomorrow', 'today', 'monday', 'tuesday', 'wednesday', 'thursday', 
        'friday', 'saturday', 'sunday', 'week', 'month', 'year',
        'at', 'am', 'pm', 'morning', 'afternoon', 'evening', 'night',
        'january', 'february', 'march', 'april', 'may', 'june', 'july',
        'august', 'september', 'october', 'november', 'december'
    ]
    
    # Also check for time patterns like "2pm", "3:30", etc.
    time_pattern = r'\b(\d{1,2}(:\d{2})?\s*(am|pm)?)\b'
    has_time = re.search(time_pattern, message_lower)
    
    has_date_word = any(word in message_lower for word in time_date_words)
    
    # If message has time/date reference and is more than 3 words, assume event creation
    if (has_time or has_date_word) and len(message.split()) >= 3:
        print(f"✅ Triggering AI event creation: time={has_time}, date_word={has_date_word}")
        event_service = EventCreationService(user)
        return event_service.process_event_creation(message)
    
    # Also trigger on explicit creation keywords
    create_keywords = ['create', 'schedule', 'appointment', 'meeting', 'remind', 'set up']
    if any(keyword in message_lower for keyword in create_keywords):
        print("✅ Triggering AI via creation keyword")
        event_service = EventCreationService(user)
        return event_service.process_event_creation(message)
    
    print("❌ No trigger matched, falling back to default")  # DEBUG
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
        return "You have no upcoming events! 🎉\n\nTry creating one with: 'Team meeting tomorrow at 3pm'"
    
    response = "📅 *Your Upcoming Events:*\n\n"
    for event in upcoming_events:
        time_str = event.scheduled_time.strftime('%a, %b %d at %I:%M %p')
        location_str = f" @ {event.location}" if event.location else ""
        response += f"• *{event.title}*\n  {time_str}{location_str}\n\n"
    
    response += "To create a new event, just tell me about it! ✨"
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
        return "No events scheduled for today! 🕶️\n\nEnjoy your free time! You can schedule events with natural language."
    
    response = f"📋 *Today's Agenda ({today.strftime('%A, %b %d')}):*\n\n"
    for event in todays_events:
        time_str = event.scheduled_time.strftime('%I:%M %p')
        location_str = f" @ {event.location}" if event.location else ""
        response += f"• *{time_str}* - {event.title}{location_str}\n"
    
    return response


def health(request):
    return JsonResponse({"message" : "Welcome to Isele"})