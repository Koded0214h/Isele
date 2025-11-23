# core/event_creator.py
from .models import Event, EventManagerUser
from .ai_service import ai_service
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EventCreationService:
    def __init__(self, user):
        self.user = user
    
    def process_event_creation(self, message: str) -> str:
        """Process event creation flow with AI assistance"""
        
        # Check if we're in the middle of an event creation conversation
        conversation_state = self.user.current_conversation_state or {}
        
        if conversation_state.get('creating_event'):
            return self._continue_event_creation(message, conversation_state)
        else:
            return self._start_event_creation(message)
    
    def _start_event_creation(self, message: str) -> str:
        """Start new event creation with AI parsing"""
        
        # Use AI to parse the event details
        event_data = ai_service.parse_event_message(message)
        
        if event_data['confidence'] < 0.6 or event_data['needs_clarification']:
            # Ask for clarification
            clarification = event_data.get('clarification_question', 
                                         "Could you provide more details about the event?")
            
            # Save conversation state
            self.user.current_conversation_state = {
                'creating_event': True,
                'pending_event': event_data,
                'step': 'clarification'
            }
            self.user.save()
            
            return f"🤔 {clarification}"
        
        # Try to create the event with parsed data
        return self._create_event_from_data(event_data)
    
    def _continue_event_creation(self, message: str, conversation_state: dict) -> str:
        """Continue event creation based on previous state"""
        
        if conversation_state.get('step') == 'clarification':
            # Combine original data with clarification
            pending_event = conversation_state['pending_event']
            
            # Re-parse with the new information
            combined_message = f"{pending_event.get('title', 'Event')} {message}"
            event_data = ai_service.parse_event_message(combined_message)
            
            if event_data['confidence'] >= 0.6 and not event_data['needs_clarification']:
                # Clear conversation state
                self.user.clear_conversation_state()
                return self._create_event_from_data(event_data)
            else:
                # Still need clarification
                clarification = event_data.get('clarification_question', 
                                             "I'm still not sure. Could you be more specific?")
                
                # Update pending event data if AI provided better context
                self.user.current_conversation_state = {
                    'creating_event': True,
                    'pending_event': event_data,
                    'step': 'clarification'
                }
                self.user.save()

                return f"🤔 {clarification}"
        
        # Default: clear state and start over
        self.user.clear_conversation_state()
        return "Let's try again. What event would you like to create?"
    
    def _create_event_from_data(self, event_data: dict) -> str:
        """Create event from parsed data and return response message"""
        try:
            # Validate required fields
            if not event_data.get('title'):
                return "❌ I couldn't determine the event title. Please try again with a clearer description."
            
            # In a real-world scenario, you might relax this if the user is just asking for a reminder without a specific time
            if not event_data.get('datetime'):
                return "❌ I couldn't determine the event time. Please specify when this should happen."
            
            # Create the event
            event = Event.objects.create(
                user=self.user,
                title=event_data['title'],
                scheduled_time=event_data['datetime'],
                location=event_data.get('location'),
                notes=event_data.get('notes', '') # <-- SAVING NOTES
            )
            
            # Format success message
            time_str = event.scheduled_time.strftime('%A, %b %d at %I:%M %p')
            location_str = f" at {event.location}" if event.location else ""
            # Display notes if they exist
            notes_str = f"\n📄 Notes: {event.notes}" if event.notes else ""
            
            return f"✅ *Event Created Successfully!* 🎉\n\n" \
                   f"*{event.title}*\n" \
                   f"📅 {time_str}{location_str}{notes_str}\n\n" \
                   f"Use 'events' to see all your upcoming events!"
                   
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return "❌ Sorry, I couldn't create that event. Please try again with different details."