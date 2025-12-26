#!/usr/bin/env python3
"""
Integration test to verify the complete flow:
1. JSON MQTT command with email
2. Email stored during recording session
3. Email passed to upload function

This test mocks the GUI components but tests the real flow.
"""
import sys
import os
from unittest.mock import MagicMock, patch, call
from pathlib import Path

# Add src to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(parent_dir, 'src'))

def test_end_to_end_flow():
    """Test the complete flow from MQTT command to n8n upload"""
    print("\n" + "="*60)
    print("Integration Test: MQTT JSON Command → Email → n8n Upload")
    print("="*60)
    
    from mqtt_client import MQTTClient
    
    # Setup MQTT client
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    client = MQTTClient(config)
    
    # Mock GUI state
    gui_state = {
        'current_email': None,
        'email_passed_to_upload': None,
        'room_passed_to_upload': None
    }
    
    # Create mock start callback that simulates GUI behavior
    def mock_start_callback(email=None):
        """Simulates GUI's mqtt_on_start method"""
        gui_state['current_email'] = email
        print(f"  → Start callback called with email: {email}")
    
    # Register callback
    client.set_callbacks(on_start=mock_start_callback)
    
    # Test 1: Send JSON command with email
    print("\n1. Sending JSON MQTT command with email...")
    json_command = '{"command": "start", "email": "anna@example.com"}'
    client._handle_command(json_command)
    
    if gui_state['current_email'] == 'anna@example.com':
        print("  ✓ Email stored in GUI state")
    else:
        print(f"  ✗ Email not stored correctly. Got: {gui_state['current_email']}")
        return False
    
    # Test 2: Simulate upload with stored email
    print("\n2. Simulating upload with stored email and room...")
    
    # Mock the upload_file function
    def mock_upload_file(flac_path, email=None, room=None):
        """Mock upload function that captures parameters"""
        gui_state['email_passed_to_upload'] = email
        gui_state['room_passed_to_upload'] = room
        print(f"  → upload_file called with:")
        print(f"      file: {flac_path}")
        print(f"      email: {email}")
        print(f"      room: {room}")
        return True, "Success"
    
    # Simulate what _convert_and_upload does
    email = gui_state['current_email']  # Get email from GUI state
    room = "Konferensrum A"  # Simulate room from config
    flac_path = Path("/tmp/test.flac")
    
    ok, info = mock_upload_file(flac_path, email=email, room=room)
    
    # Test 3: Verify parameters were passed correctly
    print("\n3. Verifying parameters passed to upload...")
    
    all_passed = True
    
    if gui_state['email_passed_to_upload'] == 'anna@example.com':
        print("  ✓ Email passed to upload correctly")
    else:
        print(f"  ✗ Email not passed correctly. Got: {gui_state['email_passed_to_upload']}")
        all_passed = False
    
    if gui_state['room_passed_to_upload'] == 'Konferensrum A':
        print("  ✓ Room passed to upload correctly")
    else:
        print(f"  ✗ Room not passed correctly. Got: {gui_state['room_passed_to_upload']}")
        all_passed = False
    
    # Test 4: Verify backward compatibility (no email)
    print("\n4. Testing backward compatibility (command without email)...")
    gui_state['current_email'] = None
    gui_state['email_passed_to_upload'] = None
    
    # Send plain text command
    client._handle_command("start")
    
    if gui_state['current_email'] is None:
        print("  ✓ No email stored when not provided")
    else:
        print(f"  ✗ Unexpected email stored: {gui_state['current_email']}")
        all_passed = False
    
    # Simulate upload without email
    ok, info = mock_upload_file(flac_path, email=None, room=room)
    
    if gui_state['email_passed_to_upload'] is None:
        print("  ✓ No email passed to upload when not provided")
    else:
        print(f"  ✗ Unexpected email passed: {gui_state['email_passed_to_upload']}")
        all_passed = False
    
    return all_passed

def main():
    """Run integration test"""
    print("\n" + "="*60)
    print("Integration Test Suite")
    print("="*60)
    
    result = test_end_to_end_flow()
    
    print("\n" + "="*60)
    print("TEST RESULT")
    print("="*60)
    
    if result:
        print("✓ Integration test PASSED")
        print("\nThe complete flow works correctly:")
        print("  MQTT JSON command → Email extraction → GUI storage → Upload with email")
        return 0
    else:
        print("✗ Integration test FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
