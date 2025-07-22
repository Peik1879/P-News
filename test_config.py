#!/usr/bin/env python3
"""
Test script to check .env configuration
"""

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print('🔍 Testing .env loading:')
print(f'ENABLE_MOBILE_NOTIFICATIONS: {os.getenv("ENABLE_MOBILE_NOTIFICATIONS")}')
print(f'PUSHBULLET_API_KEY: {os.getenv("PUSHBULLET_API_KEY", "NOT_FOUND")}')
print(f'NOTIFICATION_THRESHOLD: {os.getenv("NOTIFICATION_THRESHOLD")}')
print()

# Test notification service
if os.getenv('PUSHBULLET_API_KEY'):
    print('✅ Pushbullet API Key found!')
    
    # Test actual notification
    import requests
    import json
    
    api_key = os.getenv('PUSHBULLET_API_KEY')
    url = 'https://api.pushbullet.com/v2/pushes'
    
    data = {
        'type': 'note',
        'title': '🧪 GUI Test Notification',
        'body': 'GUI is now properly configured with Pushbullet! 📱✅'
    }
    
    headers = {
        'Access-Token': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            print('📱 SUCCESS: Test notification sent!')
        else:
            print(f'❌ ERROR: {response.status_code} - {response.text}')
    except Exception as e:
        print(f'❌ CONNECTION ERROR: {e}')
        
else:
    print('❌ Pushbullet API Key missing!')

print('\n🚀 GUI should now work with Pushbullet notifications!')
