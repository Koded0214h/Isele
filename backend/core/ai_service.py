# core/ai_service.py
from google import genai
import os
import json
import re
from datetime import datetime
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EventAIService:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        self.client = genai.Client(api_key=api_key)
        
        # System prompt for event parsing - UPDATED FOR LINK EXTRACTION AND NOTES
        self.system_instruction = """
        You are an expert event parser specializing in meeting schedules. Extract event details from the user's message and return ONLY valid JSON.
        
        CRITICAL RULE: If you find a complete meeting link (e.g., zoom.us/, meet.google.com/, teams.microsoft.com/, or any URL starting with http/https), place the entire link in the "location" field.
        
        RESPONSE FORMAT (JSON ONLY):
        {{
            "title": "Event title",
            "datetime": "YYYY-MM-DD HH:MM:SS or null if not specified",
            "location": "Location (e.g., meeting link, physical address) or null",
            "notes": "Any extra details like meeting ID, password, or general instructions. Or null.",
            "confidence": 0.8,
            "needs_clarification": false,
            "clarification_question": "What needs clarification or null"
        }}
        
        RULES:
        - Today: {today_date}
        - Current time: {current_time}
        - If time not specified, default to 12:00:00 (midday)
        - If date not specified, assume the soonest logical date (e.g., "next monday")
        - Return ONLY valid JSON, no other text or explanation.
        """
    
    def parse_event_message(self, message: str) -> dict:
        """Parse natural language message into structured event data"""
        
        # Default error response - UPDATED with 'notes' field
        default_error_response = {
            "title": None,
            "datetime": None,
            "location": None,
            "notes": None,
            "confidence": 0.0,
            "needs_clarification": True,
            "clarification_question": "I'm having trouble understanding. Could you be more specific?"
        }
        
        try:
            # Get current date/time for context
            now = timezone.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            
            # Format system instruction with current context
            system_prompt = self.system_instruction.format(
                today_date=current_date,
                current_time=current_time
            )

            # Create full prompt
            full_prompt = f"{system_prompt}\n\nUser message: {message}"

            # Generate content using the correct API
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt
            )
            
            print(f"Response object: {response}")
            
            # Extract text from response
            response_text = ""
            
            # Try multiple ways to extract the text
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    if candidate.content.parts:
                        response_text = candidate.content.parts[0].text
            
            # Fallback
            if not response_text or not response_text.strip():
                logger.error("Empty response from AI")
                print("❌ Empty response from AI")
                return default_error_response

            print(f"🤖 AI Raw Response: {response_text}")

            # Clean the response - remove markdown code blocks if present
            response_text = re.sub(r'```json\s*|\s*```', '', response_text).strip()
            
            # Also remove any markdown formatting
            response_text = re.sub(r'```\s*', '', response_text).strip()

            print(f"Cleaned response text: '{response_text}'")
            
            # Parse JSON response
            event_data = json.loads(response_text)
            
            # Convert datetime string to timezone-aware datetime object
            if event_data.get('datetime') and event_data['datetime'] != 'null':
                event_data['datetime'] = self._parse_datetime_string(event_data['datetime'])
            else:
                event_data['datetime'] = None
            
            print(f"📊 Parsed Event Data: {event_data}")
            return event_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text if 'response_text' in locals() else 'N/A'}")
            print(f"❌ JSON Parse Error: {e}")
            return default_error_response
        except AttributeError as e:
            logger.error(f"Attribute error accessing response: {e}")
            print(f"❌ Attribute Error: {e}")
            return default_error_response
        except Exception as e:
            logger.error(f"AI service error: {e}")
            print(f"❌ AI Service Error: {e}")
            return default_error_response
    
    def _parse_datetime_string(self, datetime_str: str):
        """Convert datetime string to timezone-aware datetime object"""
        try:
            # Handle null case
            if datetime_str is None or datetime_str.lower() == "null":
                return None
                
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
                        dt = timezone.make_aware(dt, timezone.get_current_timezone())
                    return dt
                except ValueError:
                    continue
            
            # If none of the formats work, return None
            print(f"❌ Could not parse datetime string: {datetime_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing datetime string: {e}")
            return None

# Global instance
ai_service = EventAIService()