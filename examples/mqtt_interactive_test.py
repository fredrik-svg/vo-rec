#!/usr/bin/env python3
"""
Interactive MQTT client example to test the status command.

This script demonstrates how to:
1. Connect to an MQTT broker
2. Subscribe to device status updates
3. Send status query commands
4. Monitor responses
"""
import sys
import os
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt is not installed")
    print("Install with: pip install paho-mqtt")
    sys.exit(1)

# Configuration - modify these for your broker
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "meetrec/device1")
USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() in ("true", "1", "yes")

def normalize_topic_prefix(prefix):
    """Normalize topic prefix"""
    if not prefix:
        return "meetrec/device"
    normalized = prefix.replace(" ", "")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    normalized = normalized.lstrip("/").rstrip("/")
    return normalized or "meetrec/device"

TOPIC_PREFIX = normalize_topic_prefix(TOPIC_PREFIX)
TOPIC_COMMAND = f"{TOPIC_PREFIX}/command"
TOPIC_STATUS = f"{TOPIC_PREFIX}/status"
TOPIC_CONFIG = f"{TOPIC_PREFIX}/config"
TOPIC_RECORDING = f"{TOPIC_PREFIX}/recording"

# Track received messages
received_messages = []

def on_connect(client, userdata, flags, rc):
    """Callback when connected to broker"""
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {BROKER}:{PORT}")
        print(f"✓ Subscribing to: {TOPIC_PREFIX}/#")
        client.subscribe(f"{TOPIC_PREFIX}/#")
    else:
        print(f"✗ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when message is received"""
    topic = msg.topic
    try:
        payload = msg.payload.decode('utf-8')
        # Try to parse as JSON for pretty printing
        try:
            data = json.loads(payload)
            payload_str = json.dumps(data, indent=2)
        except:
            payload_str = payload
        
        timestamp = time.strftime("%H:%M:%S")
        print(f"\n[{timestamp}] Message received on '{topic}':")
        print(payload_str)
        print("-" * 60)
        
        received_messages.append({
            "topic": topic,
            "payload": payload,
            "timestamp": timestamp
        })
    except Exception as e:
        print(f"Error processing message: {e}")

def send_command(client, command, email=None):
    """Send a command to the device"""
    if email:
        payload = json.dumps({"command": command, "email": email})
    else:
        payload = json.dumps({"command": command})
    
    print(f"\n→ Sending command: {payload}")
    result = client.publish(TOPIC_COMMAND, payload)
    if result.rc == 0:
        print(f"✓ Command sent to {TOPIC_COMMAND}")
    else:
        print(f"✗ Failed to send command: {result.rc}")
    return result.rc == 0

def interactive_menu(client):
    """Interactive menu for testing commands"""
    print("\n" + "=" * 60)
    print("MQTT Status Command Test - Interactive Mode")
    print("=" * 60)
    print(f"Broker: {BROKER}:{PORT}")
    print(f"Topic Prefix: {TOPIC_PREFIX}")
    print("=" * 60)
    
    while True:
        print("\nCommands:")
        print("  1 - Request status (JSON format)")
        print("  2 - Request status (text format)")
        print("  3 - Start recording")
        print("  4 - Start recording with email")
        print("  5 - Stop recording")
        print("  6 - Toggle test")
        print("  7 - Show received messages")
        print("  8 - Clear received messages")
        print("  q - Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == '1':
            send_command(client, "status")
            print("Waiting for status response...")
            time.sleep(1)
        
        elif choice == '2':
            print(f"\n→ Sending text command: status")
            result = client.publish(TOPIC_COMMAND, "status")
            if result.rc == 0:
                print(f"✓ Command sent to {TOPIC_COMMAND}")
                print("Waiting for status response...")
                time.sleep(1)
            else:
                print(f"✗ Failed to send command: {result.rc}")
        
        elif choice == '3':
            send_command(client, "start")
        
        elif choice == '4':
            email = input("Enter email: ").strip()
            send_command(client, "start", email)
        
        elif choice == '5':
            send_command(client, "stop")
        
        elif choice == '6':
            send_command(client, "test")
        
        elif choice == '7':
            print("\nReceived Messages:")
            print("=" * 60)
            if not received_messages:
                print("No messages received yet")
            else:
                for i, msg in enumerate(received_messages, 1):
                    print(f"\n{i}. [{msg['timestamp']}] {msg['topic']}:")
                    try:
                        data = json.loads(msg['payload'])
                        print(json.dumps(data, indent=2))
                    except:
                        print(msg['payload'])
            print("=" * 60)
        
        elif choice == '8':
            received_messages.clear()
            print("✓ Messages cleared")
        
        elif choice == 'q':
            print("\nDisconnecting...")
            client.disconnect()
            break
        
        else:
            print("Invalid choice")

def main():
    """Main function"""
    print("MQTT Status Command Test")
    print("=" * 60)
    
    # Create client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set credentials if provided
    if USERNAME and PASSWORD:
        print(f"Using authentication: {USERNAME}")
        client.username_pw_set(USERNAME, PASSWORD)
    
    # Set TLS if enabled
    if USE_TLS:
        import ssl
        print("TLS enabled")
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    
    try:
        # Connect to broker
        print(f"Connecting to {BROKER}:{PORT}...")
        client.connect(BROKER, PORT, 60)
        
        # Start network loop in background
        client.loop_start()
        
        # Wait for connection
        time.sleep(2)
        
        # Run interactive menu
        interactive_menu(client)
        
        # Stop loop
        client.loop_stop()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    print("Done!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
