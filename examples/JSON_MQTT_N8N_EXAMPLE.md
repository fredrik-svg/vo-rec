# Example: Using JSON MQTT Commands with Email for n8n Integration

This example shows how to use the new JSON MQTT command format to start recordings with email addresses and have them automatically sent to the correct recipient via n8n.

## Overview

The new JSON command format allows you to specify an email address when starting a recording. This email is then:
1. Stored during the recording session
2. Sent to n8n along with the file when the recording completes
3. Used by n8n to send the transcription/summary to the right person

## MQTT Command Format

### Start Recording with Email (JSON format)
```bash
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/command" \
  -m '{"command": "start", "email": "anna@example.com"}'
```

### Start Recording without Email (JSON format)
```bash
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/command" \
  -m '{"command": "start"}'
```

### Start Recording (Plain text - backward compatible)
```bash
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/command" \
  -m "start"
```

### Stop Recording
```bash
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/command" \
  -m '{"command": "stop"}'
```

## n8n Webhook Payload

When the recording completes and is uploaded to n8n, the webhook receives:

**Multipart Form Data:**
```
file: [Binary FLAC audio file]
filename: "meeting-20251223-140530.flac"
email: "anna@example.com"          (if provided in start command)
room: "Konferensrum A"              (from DEVICE_ROOM config)
```

## Example n8n Workflow

Here's a complete n8n workflow that receives recordings and sends them to users:

### 1. Webhook Node
- **Method:** POST
- **Path:** `/webhook/meetrec`
- **Response Mode:** Immediately

### 2. Set Variables Node
Extract metadata from the request:
```json
{
  "filename": "{{ $json.filename }}",
  "email": "{{ $json.email }}",
  "room": "{{ $json.room }}",
  "file": "{{ $binary.file }}"
}
```

### 3. Whisper AI / Transcription Node
Transcribe the audio file:
- **Input Binary Field:** `file`
- **Output:** Transcription text

### 4. OpenAI / Summary Node (Optional)
Create a summary:
- **Prompt:** "Summarize this meeting transcript: {{ $json.transcription }}"

### 5. Email Node
Send to the user:
- **To:** `{{ $node["Set Variables"].json.email }}`
- **Subject:** `Meeting Recording from {{ $node["Set Variables"].json.room }}`
- **Body:**
```
Hello,

Your meeting recording from {{ $node["Set Variables"].json.room }} is ready.

Filename: {{ $node["Set Variables"].json.filename }}

Transcription:
{{ $json.transcription }}

Summary:
{{ $json.summary }}

Best regards,
Meeting Recorder System
```

### 6. Save to Google Drive Node (Optional)
- **File Name:** `{{ $node["Set Variables"].json.filename }}`
- **Parents:** Shared folder ID

## Configuration

### 1. Raspberry Pi Configuration (.env)
```bash
# MQTT Settings
MQTT_ENABLED=true
MQTT_BROKER=mqtt.example.com
MQTT_PORT=8883
MQTT_USERNAME=meetrec_device
MQTT_PASSWORD=secure_password
MQTT_TOPIC_PREFIX=meetrec/device1
MQTT_USE_TLS=true

# Device Settings
DEVICE_ROOM=Konferensrum A
DEVICE_EMAIL=default@example.com  # Fallback if not specified in command

# Upload Target
UPLOAD_TARGET=n8n
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/meetrec
```

### 2. Test the Setup

Start a recording with email:
```bash
mosquitto_pub -h mqtt.example.com -p 8883 \
  -u meetrec_device -P secure_password \
  --capath /etc/ssl/certs/ \
  -t "meetrec/device1/command" \
  -m '{"command": "start", "email": "test@example.com"}'
```

Stop the recording:
```bash
mosquitto_pub -h mqtt.example.com -p 8883 \
  -u meetrec_device -P secure_password \
  --capath /etc/ssl/certs/ \
  -t "meetrec/device1/command" \
  -m '{"command": "stop"}'
```

Monitor status:
```bash
mosquitto_sub -h mqtt.example.com -p 8883 \
  -u meetrec_device -P secure_password \
  --capath /etc/ssl/certs/ \
  -t "meetrec/device1/#"
```

## Home Assistant Integration

Automate recordings based on calendar events:

```yaml
automation:
  - alias: "Start Meeting Recording with Attendee Email"
    trigger:
      - platform: state
        entity_id: calendar.meetings
        to: "on"
    action:
      - service: mqtt.publish
        data:
          topic: "meetrec/device1/command"
          payload: >
            {
              "command": "start",
              "email": "{{ state_attr('calendar.meetings', 'organizer_email') }}"
            }
  
  - alias: "Stop Meeting Recording"
    trigger:
      - platform: state
        entity_id: calendar.meetings
        to: "off"
    action:
      - service: mqtt.publish
        data:
          topic: "meetrec/device1/command"
          payload: '{"command": "stop"}'
```

## Python Example

```python
import paho.mqtt.client as mqtt
import json

# MQTT settings
BROKER = "mqtt.example.com"
PORT = 8883
USERNAME = "meetrec_device"
PASSWORD = "secure_password"
TOPIC = "meetrec/device1/command"

# Create MQTT client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()  # Enable TLS

# Connect to broker
client.connect(BROKER, PORT, 60)

# Start recording with email
command = {
    "command": "start",
    "email": "anna@example.com"
}
client.publish(TOPIC, json.dumps(command))

# ... wait for meeting to end ...

# Stop recording
stop_command = {"command": "stop"}
client.publish(TOPIC, json.dumps(stop_command))

# Disconnect
client.disconnect()
```

## Troubleshooting

### Email not received in n8n
1. Check that MQTT command was sent correctly (with email field)
2. Verify n8n webhook is receiving the data:
   - Check n8n execution log
   - Look for `email` field in webhook payload
3. Check n8n email node configuration:
   - Ensure `To` field references correct variable
   - Test with a static email first

### Backward Compatibility
If you want to use plain text commands (without JSON), you can still do:
```bash
mosquitto_pub -t "meetrec/device1/command" -m "start"
mosquitto_pub -t "meetrec/device1/command" -m "stop"
```

In this case, n8n will receive:
- `filename`: Recording filename
- `room`: Room from DEVICE_ROOM config
- `email`: Empty or from DEVICE_EMAIL config

### Testing n8n Webhook Locally

You can test the n8n webhook format using curl:
```bash
curl -X POST https://your-n8n.com/webhook/meetrec \
  -F "file=@test.flac" \
  -F "filename=test.flac" \
  -F "email=test@example.com" \
  -F "room=Test Room"
```
