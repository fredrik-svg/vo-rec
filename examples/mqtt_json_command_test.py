#!/usr/bin/env python3
"""
Test script to verify JSON MQTT command handling with email support.

This script tests:
1. JSON command parsing ({"command": "start", "email": "user@example.com"})
2. Email extraction from JSON commands
3. Backward compatibility with plain text commands
4. Email parameter passing to callbacks
"""
import sys
import json
import logging
from unittest.mock import MagicMock, call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import MQTT client - add parent directory to path
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(parent_dir, 'src'))
from mqtt_client import MQTTClient

def test_json_command_parsing():
    """Test JSON command parsing with email"""
    print("\n" + "="*60)
    print("TEST 1: JSON Command Parsing with Email")
    print("="*60)
    
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    client = MQTTClient(config)
    
    # Create mock callback
    on_start_mock = MagicMock()
    client.set_callbacks(on_start=on_start_mock)
    
    # Test JSON command with email
    all_passed = True
    json_payload = json.dumps({"command": "start", "email": "anna@example.com"})
    client._handle_command(json_payload)
    
    if on_start_mock.called:
        print("✓ JSON command triggers callback")
        # Check if email was passed as keyword argument
        if on_start_mock.call_args.kwargs.get('email') == 'anna@example.com':
            print("✓ Email extracted and passed to callback: anna@example.com")
        else:
            print(f"✗ Email not passed correctly. Got: {on_start_mock.call_args}")
            all_passed = False
    else:
        print("✗ JSON command does not trigger callback")
        all_passed = False
    
    return all_passed

def test_json_command_without_email():
    """Test JSON command without email"""
    print("\n" + "="*60)
    print("TEST 2: JSON Command Without Email")
    print("="*60)
    
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    client = MQTTClient(config)
    
    # Create mock callback
    on_start_mock = MagicMock()
    client.set_callbacks(on_start=on_start_mock)
    
    # Test JSON command without email
    all_passed = True
    json_payload = json.dumps({"command": "start"})
    client._handle_command(json_payload)
    
    if on_start_mock.called:
        print("✓ JSON command without email triggers callback")
        # Callback should be called without email parameter or with empty email
        print(f"  Callback args: {on_start_mock.call_args}")
    else:
        print("✗ JSON command without email does not trigger callback")
        all_passed = False
    
    return all_passed

def test_backward_compatibility_text_commands():
    """Test backward compatibility with plain text commands"""
    print("\n" + "="*60)
    print("TEST 3: Backward Compatibility with Text Commands")
    print("="*60)
    
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    client = MQTTClient(config)
    
    # Create mock callbacks
    on_start_mock = MagicMock()
    on_stop_mock = MagicMock()
    on_test_mock = MagicMock()
    
    client.set_callbacks(
        on_start=on_start_mock,
        on_stop=on_stop_mock,
        on_test=on_test_mock
    )
    
    all_passed = True
    
    # Test plain text "start"
    client._handle_command("start")
    if on_start_mock.called:
        print("✓ Plain text 'start' command works (backward compatible)")
    else:
        print("✗ Plain text 'start' command does not work")
        all_passed = False
    on_start_mock.reset_mock()
    
    # Test plain text "stop"
    client._handle_command("stop")
    if on_stop_mock.called:
        print("✓ Plain text 'stop' command works (backward compatible)")
    else:
        print("✗ Plain text 'stop' command does not work")
        all_passed = False
    on_stop_mock.reset_mock()
    
    # Test plain text "test"
    client._handle_command("test")
    if on_test_mock.called:
        print("✓ Plain text 'test' command works (backward compatible)")
    else:
        print("✗ Plain text 'test' command does not work")
        all_passed = False
    
    return all_passed

def test_various_json_formats():
    """Test various JSON formats and edge cases"""
    print("\n" + "="*60)
    print("TEST 4: Various JSON Formats and Edge Cases")
    print("="*60)
    
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    client = MQTTClient(config)
    on_start_mock = MagicMock()
    on_stop_mock = MagicMock()
    client.set_callbacks(on_start=on_start_mock, on_stop=on_stop_mock)
    
    all_passed = True
    
    # Test case 1: Stop command in JSON format
    test_cases = [
        (json.dumps({"command": "stop"}), "stop", on_stop_mock, "Stop command in JSON format"),
        (json.dumps({"command": "start", "email": "test@test.com"}), "start", on_start_mock, "Start with email"),
        (json.dumps({"command": "START", "email": "TEST@TEST.COM"}), "start", on_start_mock, "Uppercase command"),
        (json.dumps({"command": "start", "email": ""}), "start", on_start_mock, "Empty email string"),
    ]
    
    for payload, expected_cmd, mock_obj, description in test_cases:
        mock_obj.reset_mock()
        try:
            client._handle_command(payload)
            if mock_obj.called:
                print(f"✓ {description}")
            else:
                print(f"✗ {description} - callback not called")
                all_passed = False
        except Exception as e:
            print(f"✗ {description} - Exception: {e}")
            all_passed = False
    
    return all_passed

def test_invalid_json_fallback():
    """Test fallback to text parsing for invalid JSON"""
    print("\n" + "="*60)
    print("TEST 5: Invalid JSON Fallback to Text Parsing")
    print("="*60)
    
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    client = MQTTClient(config)
    on_start_mock = MagicMock()
    client.set_callbacks(on_start=on_start_mock)
    
    all_passed = True
    
    # Test invalid JSON that should fallback to text parsing
    invalid_json_cases = [
        ("start", "Plain text 'start'", True),
        ("START", "Uppercase 'START'", True),
        ("{invalid json}", "Invalid JSON without command", False),
    ]
    
    for payload, description, should_trigger in invalid_json_cases:
        on_start_mock.reset_mock()
        try:
            client._handle_command(payload)
            if should_trigger:
                if on_start_mock.called:
                    print(f"✓ {description} - fallback to text parsing works")
                else:
                    print(f"✗ {description} - fallback did not trigger callback")
                    all_passed = False
            else:
                if not on_start_mock.called:
                    print(f"✓ {description} - correctly ignored")
                else:
                    print(f"✗ {description} - should not trigger callback")
                    all_passed = False
        except Exception as e:
            print(f"✗ {description} - Exception: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("JSON MQTT Command Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("JSON Command Parsing with Email", test_json_command_parsing()))
    results.append(("JSON Command Without Email", test_json_command_without_email()))
    results.append(("Backward Compatibility", test_backward_compatibility_text_commands()))
    results.append(("Various JSON Formats", test_various_json_formats()))
    results.append(("Invalid JSON Fallback", test_invalid_json_fallback()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
