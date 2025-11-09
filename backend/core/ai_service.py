import google.generativeai as genai
import os
import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EventAIService:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # System prompt for event parsing
        self.system_prompt = """
        You are an expert event parser. Extract event details from natural language and return ONLY valid JSON.
        
        RESPONSE FORMAT:
        {
            "title": "Event title",
            "datetime": "YYYY-MM-DD HH:MM:SS or null if not specified",
            "location": "Location or null",
            "confidence": 0.8,
            "needs_clarification": false,
            "clarification_question": "What needs clarification or null"
        }
        
        DATE/TIME HANDLING:
        - Today: {today_date}
        - Current time: {current_time}
        - If time not specified, default to 12:00:00
        - If date not specified, assume soonest logical date
        
        Return valid JSON only, no other text.
        """
    
    def parse_event_message(self, message: str) -> dict:
        """Parse natural language message into structured event data"""
        try:
            # Get current date/time for context
            now = timezone.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            
            prompt = self.system_prompt.format(
                today_date=current_date,
                current_time=current_time
            )
            
            full_prompt = f"{prompt}\n\nUser message: {message}"
            
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            # Clean the response - remove markdown code blocks if present
            response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            
            # Parse JSON response
            event_data = json.loads(response_text)
            
            # Convert datetime string to timezone-aware datetime object
            if event_data.get('datetime'):
                event_data['datetime'] = self._parse_datetime_string(event_data['datetime'])
            
            return event_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text}")
            return {
                "title": None,
                "datetime": None,
                "location": None,
                "confidence": 0.0,
                "needs_clarification": True,
                "clarification_question": "I couldn't understand the event details. Could you rephrase?"
            }
        except Exception as e:
            logger.error(f"AI service error: {e}")
            return {
                "title": None,
                "datetime": None,
                "location": None,
                "confidence": 0.0,
                "needs_clarification": True,
                "clarification_question": "I'm having trouble understanding. Could you be more specific?"
            }
    
    def _parse_datetime_string(self, datetime_str: str):
        """Convert datetime string to timezone-aware datetime object"""
        try:
            # Try different datetime formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(datetime_str, fmt)
                    # Make it timezone-aware
                    if timezone.is_naive(dt):
                        dt = timezone.make_aware(dt)
                    return dt
                except ValueError:
                    continue
            
            # If none of the formats work, return None
            return None
            
        except Exception as e:
            logger.error(f"Error parsing datetime string: {e}")
            return None

# Global instance
ai_service = EventAIService()