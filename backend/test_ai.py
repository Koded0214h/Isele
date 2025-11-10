import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.ai_service import ai_service

# Test the AI service directly
test_messages = [
    "Meeting with Blessing tomorrow at 5am",
    "Team meeting at 3pm tomorrow",
    "Lunch with Sarah on Friday",
    "Dentist appointment next Monday at 2pm"
]

print("🧪 Testing AI Service...")
for message in test_messages:
    print(f"\n--- Testing: '{message}' ---")
    try:
        result = ai_service.parse_event_message(message)
        print(f"✅ Success: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")