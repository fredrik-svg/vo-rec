# MQTT/HiveMQ Cloud Integration - Testing Guide

## Overview
This guide explains how to test the MQTT integration with HiveMQ Cloud.

## Prerequisites
1. Python 3.7 or later
2. paho-mqtt library installed (`pip install paho-mqtt`)
3. HiveMQ Cloud account (free tier available)

## Setup Steps

### 1. Create HiveMQ Cloud Account
1. Go to https://www.hivemq.com/mqtt-cloud-broker/
2. Sign up for a free account
3. Create a new cluster:
   - Choose a cluster name
   - Select a region (e.g., EU, US)
   - Use the free tier for testing
4. Wait for cluster to be created (takes 1-2 minutes)

### 2. Create MQTT Credentials
1. In HiveMQ Cloud Console, go to **Access Management**
2. Click **Add New Credentials**
3. Enter a username and password
4. Set permissions:
   - **Publish**: Allow on topic `recordings/meetings/#`
   - **Subscribe**: Allow on topic `recordings/meetings/#`
5. Save credentials

### 3. Configure the Application
1. Copy `.env.mqtt.example` to `.env`:
   ```bash
   cp .env.mqtt.example .env
   ```

2. Edit `.env` and update:
   ```bash
   UPLOAD_TARGET=mqtt
   MQTT_BROKER=xxxxxxxx.s1.eu.hivemq.cloud  # Your cluster URL
   MQTT_PORT=8883
   MQTT_USERNAME=your-username
   MQTT_PASSWORD=your-password
   MQTT_TOPIC=recordings/meetings
   MQTT_USE_TLS=true
   ```

### 4. Test the Configuration

#### Method 1: Using HiveMQ Cloud Web Client
1. In HiveMQ Cloud Console, go to **Web Client**
2. Click **Connect**
3. Subscribe to topic: `recordings/meetings`
4. Run a recording with the application
5. You should see the JSON message appear in the web client

#### Method 2: Using mosquitto_sub
```bash
mosquitto_sub -h xxxxxxxx.s1.eu.hivemq.cloud -p 8883 \
  -u "your-username" -P "your-password" \
  -t "recordings/meetings" --capath /etc/ssl/certs/
```

#### Method 3: Using Python Script
```python
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("recordings/meetings")

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}:")
    print(msg.payload.decode())

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set("your-username", "your-password")
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message

client.connect("xxxxxxxx.s1.eu.hivemq.cloud", 8883, 60)
client.loop_forever()
```

## Message Format
The application publishes messages in the following JSON format:
```json
{
  "filename": "meeting-20251115-123456.flac",
  "timestamp": "2025-11-15T12:34:56.789012",
  "size": 1234567,
  "mimetype": "audio/flac",
  "data": "UklGRiQAAABXQVZFZm10IBA..." 
}
```

- **filename**: Original recording filename
- **timestamp**: ISO 8601 timestamp when recording was created
- **size**: File size in bytes (before base64 encoding)
- **mimetype**: Always "audio/flac"
- **data**: Base64-encoded FLAC file content

## Decoding the Audio File
To extract the audio file from the MQTT message:

```python
import json
import base64

# Assuming 'message' contains the JSON payload
data = json.loads(message)
audio_data = base64.b64decode(data['data'])

# Write to file
with open(data['filename'], 'wb') as f:
    f.write(audio_data)
```

## Troubleshooting

### Connection Refused
- **Issue**: Cannot connect to MQTT broker
- **Solution**: 
  - Verify broker URL is correct (no protocol prefix)
  - Check port is 8883 for TLS
  - Ensure firewall allows outbound connections on port 8883

### Authentication Failed
- **Issue**: Authentication error
- **Solution**:
  - Verify username and password are correct
  - Check credentials in HiveMQ Cloud Access Management
  - Ensure credentials have publish permissions for the topic

### TLS/SSL Error
- **Issue**: TLS handshake fails
- **Solution**:
  - Ensure `MQTT_USE_TLS=true` in .env
  - Update CA certificates: `sudo apt update && sudo apt install ca-certificates`
  - Try using TLSv1.3 instead of TLSv1.2 (edit code if needed)

### Message Not Received
- **Issue**: Message published but not received
- **Solution**:
  - Verify topic name matches exactly (case-sensitive)
  - Check topic permissions in HiveMQ Cloud
  - Ensure subscriber is connected before publishing
  - Check QoS level (should be 1 for reliable delivery)

### Large Files
- **Issue**: Large recordings fail to upload
- **Solution**:
  - HiveMQ Cloud free tier has message size limits (256KB)
  - Consider upgrading HiveMQ plan for larger messages
  - Alternative: Upload file to cloud storage and send only metadata via MQTT

## Performance Notes
- Base64 encoding increases file size by ~33%
- A 10MB FLAC file becomes ~13MB when base64-encoded
- MQTT with QoS 1 provides reliable delivery but has some overhead
- For large files, consider using MQTT only for notifications and upload files via S3/GDrive

## Security Best Practices
1. Always use TLS/SSL in production (`MQTT_USE_TLS=true`)
2. Use strong passwords for MQTT credentials
3. Limit topic permissions to only what's needed
4. Rotate credentials periodically
5. Never commit `.env` file to git (it's in `.gitignore`)
6. Use environment-specific credentials for development vs. production

## Integration Examples

### Example 1: Automatic Transcription Pipeline
Subscribe to MQTT topic → Decode audio → Send to transcription service

### Example 2: Archive to Cloud Storage
Subscribe to MQTT topic → Decode audio → Upload to S3/GDrive

### Example 3: Real-time Notifications
Subscribe to MQTT topic → Send notification (email, Slack, etc.)

### Example 4: Multi-device Recording
Multiple Raspberry Pis publish to different topics → Central processor aggregates

## Resources
- [HiveMQ Cloud Documentation](https://docs.hivemq.com/hivemq-cloud/)
- [MQTT Protocol Specification](https://mqtt.org/)
- [Paho MQTT Python Client](https://eclipse.dev/paho/files/paho.mqtt.python/html/)
- [Base64 Encoding](https://docs.python.org/3/library/base64.html)
