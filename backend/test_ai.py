# test_ai.py
import os
import django
from datetime import datetime
from django.utils import timezone
import json

# Setup Django environment for local script execution
# Adjust 'backend.settings' to your project's main settings module if needed
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup() 

# Import the updated service
from core.ai_service import EventAIService

# --- Test Cases ---
test_messages = [
    "Zoom call for the Project Kickoff on Monday at 10:30 AM. Link: [https://zoom.us/j/1234567890?pwd=xyz](https://zoom.us/j/1234567890?pwd=xyz). Meeting ID: 123 456 7890. Passcode: 54321.",
    "Schedule a quick follow-up meeting with the team next Tuesday at 4pm at the conference room.",
    "Google Meet training session this Friday 2 PM, meeting link is [meet.google.com/abc-defg-hij](https://meet.google.com/abc-defg-hij)",
    "Remind me about dinner tonight, don't forget the wine!",
]

def run_tests():
    """Runs a series of tests against the EventAIService."""
    print("🚀 Initializing Event AI Service...")
    try:
        service = EventAIService()
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Please set the GOOGLE_API_KEY environment variable.")
        return

    now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nContext Date/Time for testing: {now}")
    print("--- Running AI Parsing Tests ---")

    for i, message in enumerate(test_messages):
        print(f"\n--- Test {i+1} ---")
        print(f"Input: '{message}'")
        
        # Use the parse_event_message method
        parsed_data = service.parse_event_message(message)
        
        # Check if datetime is an object before serializing for clean print
        parsed_dt = parsed_data.get('datetime')
        if isinstance(parsed_dt, datetime):
            parsed_data['datetime'] = parsed_dt.isoformat()
        
        print("\n✨ Parsed Output (JSON):")
        print(json.dumps(parsed_data, indent=4))
        print("--------------------")

if __name__ == "__main__":
    run_tests()