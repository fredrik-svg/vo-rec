# MQTT Topics and Workflow

## Topic Structure

```
meetrec/device1/
├── command           (subscribe) - Receive control commands
├── status            (publish)   - Device status updates
├── config            (publish)   - Current configuration
├── config/set        (subscribe) - Configuration updates
└── recording         (publish)   - Recording completion info
```

**Topic Normalisering:**
Topics normaliseras automatiskt för att säkerställa kompatibilitet med alla MQTT-brokers:
- Ledande snedstreck (`/`) tas bort
- Avslutande snedstreck (`/`) tas bort
- Dubbla snedstreck (`//`) ersätts med enkla (`/`)
- Mellanslag tas bort

Detta säkerställer att topics alltid är välformade och fungerar korrekt med HiveMQ Cloud och andra MQTT-brokers.

## Command Flow

### Starting a Recording

```
User/System
    |
    | publish: "start"
    v
meetrec/device1/command
    |
    v
Device receives command
    |
    v
Device starts recording
    |
    | publish: {"status": "recording", "filename": "...", "room": "..."}
    v
meetrec/device1/status
```

### Stopping and Uploading

```
User/System
    |
    | publish: "stop"
    v
meetrec/device1/command
    |
    v
Device receives command
    |
    v
Device stops recording
    |
    | publish: {"status": "processing"}
    v
meetrec/device1/status
    |
    v
Device converts WAV to FLAC
    |
    | publish: {"status": "converting"}
    v
meetrec/device1/status
    |
    v
Device uploads to cloud
    |
    | publish: {"status": "uploading"}
    v
meetrec/device1/status
    |
    v
Upload complete
    |
    | publish: {"status": "ready"}
    v
meetrec/device1/status
    |
    | publish: {"filename": "...", "upload_result": "..."}
    v
meetrec/device1/recording
```

## Configuration Update Flow

```
User/System
    |
    | publish: {"room": "Conference Room A", "email": "test@example.com"}
    v
meetrec/device1/config/set
    |
    v
Device receives config update
    |
    v
Device updates config file
    |
    | publish: {"room": "Conference Room A", "email": "test@example.com", ...}
    v
meetrec/device1/config
```

## Status Values

| Status | Description |
|--------|-------------|
| `ready` | Device is ready to record |
| `recording` | Recording in progress |
| `processing` | Stopped, processing file |
| `converting` | Converting WAV to FLAC |
| `uploading` | Uploading to cloud |
| `error` | An error occurred |

## Command Messages

| Command | Description |
|---------|-------------|
| `start` | Start a new recording |
| `stop` | Stop current recording and upload |
| `test` | Toggle audio level testing |

## Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `room` | string | Room identifier |
| `email` | string | Email for notifications |
| `webhook_url` | string | Custom webhook URL |
| `upload_target` | string | Upload destination (s3, http, n8n) |
| `n8n_webhook_url` | string | n8n workflow webhook |
| `wifi_ssid` | string | WiFi network name |
| `wifi_password` | string | WiFi password (stored securely) |

## Example: Home Assistant Automation

```yaml
automation:
  - alias: "Start meeting recording"
    trigger:
      - platform: state
        entity_id: calendar.meetings
        to: "on"
    action:
      - service: mqtt.publish
        data:
          topic: "meetrec/device1/command"
          payload: "start"
  
  - alias: "Stop meeting recording"
    trigger:
      - platform: state
        entity_id: calendar.meetings
        to: "off"
    action:
      - service: mqtt.publish
        data:
          topic: "meetrec/device1/command"
          payload: "stop"
  
  - alias: "Notify on recording complete"
    trigger:
      - platform: mqtt
        topic: "meetrec/device1/recording"
    action:
      - service: notify.mobile_app
        data:
          title: "Recording Complete"
          message: "{{ trigger.payload_json.filename }}"
```

## Example: Node-RED Flow

```json
[
  {
    "id": "mqtt-in",
    "type": "mqtt in",
    "topic": "meetrec/device1/status",
    "name": "Device Status"
  },
  {
    "id": "filter-ready",
    "type": "switch",
    "property": "payload.status",
    "rules": [{"t": "eq", "v": "ready"}]
  },
  {
    "id": "send-notification",
    "type": "function",
    "func": "msg.payload = 'Recording device is ready';\nreturn msg;"
  }
]
```

## Security Considerations

### Authentication
```bash
# MQTT broker with authentication
MQTT_USERNAME=device1
MQTT_PASSWORD=secure_password_here
```

### TLS/SSL
```bash
# Use encrypted connection (required for HiveMQ Cloud)
MQTT_USE_TLS=true
MQTT_PORT=8883
```

### HiveMQ Cloud Configuration

HiveMQ Cloud is a managed MQTT broker that provides secure, scalable MQTT messaging:

```bash
# .env configuration for HiveMQ Cloud
MQTT_ENABLED=true
MQTT_BROKER=xxxxx.s1.eu.hivemq.cloud  # Your cluster URL from HiveMQ Console
MQTT_PORT=8883                          # HiveMQ Cloud uses TLS port
MQTT_USERNAME=your_username             # From HiveMQ Cloud credentials
MQTT_PASSWORD=your_password             # From HiveMQ Cloud credentials
MQTT_USE_TLS=true                       # Required for HiveMQ Cloud
MQTT_TLS_INSECURE=false                # Use secure certificate verification
MQTT_CLIENT_ID=meetrec_device_001      # Optional but recommended
MQTT_TOPIC_PREFIX=meetrec/device1
```

**Benefits of HiveMQ Cloud:**
- No broker installation or maintenance required
- Free tier available (100 connections, 10 GB data transfer/month)
- Built-in TLS/SSL security
- Web-based MQTT client for testing
- Global availability with multiple regions
- Automatic scaling and high availability

### ACL (Access Control List) on Broker

For self-hosted Mosquitto broker:

```
# Allow device to publish status and subscribe to commands
user device1
topic write meetrec/device1/status
topic write meetrec/device1/recording
topic write meetrec/device1/config
topic read meetrec/device1/command
topic read meetrec/device1/config/set

# Allow controller to send commands and read status
user controller1
topic read meetrec/device1/status
topic read meetrec/device1/recording
topic read meetrec/device1/config
topic write meetrec/device1/command
topic write meetrec/device1/config/set
```
