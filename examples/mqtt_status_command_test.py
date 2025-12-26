#!/usr/bin/env python3
"""
Test script to verify MQTT status command handling.

This script tests:
1. Status command parsing ({"command": "status"})
2. Status command in plain text format ("status")
3. Callback invocation for status requests
"""
import sys
import json
import logging
from unittest.mock import MagicMock

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

def test_status_command_json():
    """Test status command in JSON format"""
    print("\n" + "="*60)
    print("TEST 1: Status Command in JSON Format")
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
    on_status_mock = MagicMock()
    client.set_callbacks(on_status=on_status_mock)
    
    # Test JSON status command
    all_passed = True
    json_payload = json.dumps({"command": "status"})
    client._handle_command(json_payload)
    
    if on_status_mock.called:
        print("✓ JSON status command triggers callback")
    else:
        print("✗ JSON status command does not trigger callback")
        all_passed = False
    
    return all_passed

def test_status_command_text():
    """Test status command in plain text format"""
    print("\n" + "="*60)
    print("TEST 2: Status Command in Plain Text Format")
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
    on_status_mock = MagicMock()
    client.set_callbacks(on_status=on_status_mock)
    
    # Test plain text status command
    all_passed = True
    client._handle_command("status")
    
    if on_status_mock.called:
        print("✓ Plain text 'status' command works (backward compatible)")
    else:
        print("✗ Plain text 'status' command does not work")
        all_passed = False
    
    return all_passed

def test_status_command_uppercase():
    """Test status command with uppercase"""
    print("\n" + "="*60)
    print("TEST 3: Status Command Case Insensitive")
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
    on_status_mock = MagicMock()
    client.set_callbacks(on_status=on_status_mock)
    
    all_passed = True
    
    # Test uppercase text
    client._handle_command("STATUS")
    if on_status_mock.called:
        print("✓ Uppercase 'STATUS' command works")
    else:
        print("✗ Uppercase 'STATUS' command does not work")
        all_passed = False
    
    on_status_mock.reset_mock()
    
    # Test JSON with uppercase
    json_payload = json.dumps({"command": "STATUS"})
    client._handle_command(json_payload)
    if on_status_mock.called:
        print("✓ JSON uppercase 'STATUS' command works")
    else:
        print("✗ JSON uppercase 'STATUS' command does not work")
        all_passed = False
    
    return all_passed

def test_all_callbacks_coexist():
    """Test that all command callbacks can coexist"""
    print("\n" + "="*60)
    print("TEST 4: All Command Callbacks Coexist")
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
    on_status_mock = MagicMock()
    
    client.set_callbacks(
        on_start=on_start_mock,
        on_stop=on_stop_mock,
        on_test=on_test_mock,
        on_status=on_status_mock
    )
    
    all_passed = True
    
    # Test each command
    test_cases = [
        ("start", on_start_mock, "start"),
        ("stop", on_stop_mock, "stop"),
        ("test", on_test_mock, "test"),
        ("status", on_status_mock, "status"),
    ]
    
    for cmd, mock, description in test_cases:
        mock.reset_mock()
        client._handle_command(cmd)
        if mock.called:
            print(f"✓ '{description}' command works")
        else:
            print(f"✗ '{description}' command does not work")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MQTT Status Command Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("JSON Status Command", test_status_command_json()))
    results.append(("Text Status Command", test_status_command_text()))
    results.append(("Case Insensitive Status", test_status_command_uppercase()))
    results.append(("All Callbacks Coexist", test_all_callbacks_coexist()))
    
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
