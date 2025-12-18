#!/usr/bin/env python3
"""
Test script to verify MQTT command handling.

This script tests:
1. MQTT client initialization
2. Subscription to command topics
3. Command handling callbacks
4. Message reception and processing
"""
import sys
import time
import logging
from unittest.mock import MagicMock, patch

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

def test_mqtt_client_initialization():
    """Test that MQTT client initializes correctly"""
    print("\n" + "="*60)
    print("TEST 1: MQTT Client Initialization")
    print("="*60)
    
    config = {
        "enabled": True,
        "broker": "test.mosquitto.org",
        "port": 1883,
        "topic_prefix": "test/meetrec/device1",
        "use_tls": False,
    }
    
    try:
        client = MQTTClient(config)
        print("✓ MQTT client initialized successfully")
        print(f"  - Command topic: {client.topic_command}")
        print(f"  - Config topic: {client.topic_config_set}")
        print(f"  - Status topic: {client.topic_status}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize MQTT client: {e}")
        return False

def test_topic_normalization():
    """Test topic prefix normalization"""
    print("\n" + "="*60)
    print("TEST 2: Topic Prefix Normalization")
    print("="*60)
    
    test_cases = [
        ("/meetrec/device1/", "meetrec/device1"),
        ("meetrec//device1", "meetrec/device1"),
        (" meetrec / device1 ", "meetrec/device1"),
        ("meetrec/device1", "meetrec/device1"),
        ("", "meetrec/device"),
    ]
    
    all_passed = True
    for input_prefix, expected_output in test_cases:
        output = MQTTClient.normalize_topic_prefix(input_prefix)
        if output == expected_output:
            print(f"✓ '{input_prefix}' → '{output}'")
        else:
            print(f"✗ '{input_prefix}' → '{output}' (expected: '{expected_output}')")
            all_passed = False
    
    return all_passed

def test_callback_registration():
    """Test that callbacks are properly registered"""
    print("\n" + "="*60)
    print("TEST 3: Callback Registration")
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
    on_config_mock = MagicMock()
    
    # Register callbacks
    client.set_callbacks(
        on_start=on_start_mock,
        on_stop=on_stop_mock,
        on_test=on_test_mock,
        on_config_update=on_config_mock
    )
    
    # Verify callbacks are set
    all_passed = True
    if client.on_start_callback == on_start_mock:
        print("✓ on_start callback registered")
    else:
        print("✗ on_start callback not registered")
        all_passed = False
    
    if client.on_stop_callback == on_stop_mock:
        print("✓ on_stop callback registered")
    else:
        print("✗ on_stop callback not registered")
        all_passed = False
    
    if client.on_test_callback == on_test_mock:
        print("✓ on_test callback registered")
    else:
        print("✗ on_test callback not registered")
        all_passed = False
    
    if client.on_config_update_callback == on_config_mock:
        print("✓ on_config_update callback registered")
    else:
        print("✗ on_config_update callback not registered")
        all_passed = False
    
    return all_passed

def test_command_handling():
    """Test that command handling works correctly"""
    print("\n" + "="*60)
    print("TEST 4: Command Handling")
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
    
    # Register callbacks
    client.set_callbacks(
        on_start=on_start_mock,
        on_stop=on_stop_mock,
        on_test=on_test_mock
    )
    
    # Test commands
    all_passed = True
    
    # Test start command
    client._handle_command("start")
    if on_start_mock.called:
        print("✓ 'start' command triggers on_start callback")
    else:
        print("✗ 'start' command does not trigger on_start callback")
        all_passed = False
    on_start_mock.reset_mock()
    
    # Test stop command
    client._handle_command("stop")
    if on_stop_mock.called:
        print("✓ 'stop' command triggers on_stop callback")
    else:
        print("✗ 'stop' command does not trigger on_stop callback")
        all_passed = False
    on_stop_mock.reset_mock()
    
    # Test test command
    client._handle_command("test")
    if on_test_mock.called:
        print("✓ 'test' command triggers on_test callback")
    else:
        print("✗ 'test' command does not trigger on_test callback")
        all_passed = False
    on_test_mock.reset_mock()
    
    # Test case insensitivity
    client._handle_command("START")
    if on_start_mock.called:
        print("✓ Commands are case-insensitive")
    else:
        print("✗ Commands are not case-insensitive")
        all_passed = False
    
    # Test unknown command (should not crash)
    try:
        client._handle_command("unknown")
        print("✓ Unknown commands handled gracefully")
    except Exception as e:
        print(f"✗ Unknown commands cause exception: {e}")
        all_passed = False
    
    return all_passed

def test_message_reception():
    """Test message reception and routing"""
    print("\n" + "="*60)
    print("TEST 5: Message Reception and Routing")
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
    client.set_callbacks(on_start=on_start_mock)
    
    # Create a mock message
    mock_msg = MagicMock()
    mock_msg.topic = client.topic_command
    mock_msg.payload = b"start"
    
    # Process the message
    all_passed = True
    try:
        client._on_message(None, None, mock_msg)
        if on_start_mock.called:
            print("✓ Message routed correctly to command handler")
        else:
            print("✗ Message not routed to command handler")
            all_passed = False
    except Exception as e:
        print(f"✗ Message processing failed: {e}")
        all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("MQTT Command Handling Test Suite")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Initialization", test_mqtt_client_initialization()))
    results.append(("Topic Normalization", test_topic_normalization()))
    results.append(("Callback Registration", test_callback_registration()))
    results.append(("Command Handling", test_command_handling()))
    results.append(("Message Reception", test_message_reception()))
    
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
