# HiveMQ Cloud Support - Changes Summary

## Overview
Added full support for HiveMQ Cloud, a managed MQTT broker service that requires TLS/SSL encryption and provides enterprise-grade MQTT infrastructure.

## Changes Made

### 1. MQTT Client (`src/mqtt_client.py`)

**New Configuration Parameters:**
- `use_tls` (bool) - Enable TLS/SSL encryption
- `tls_insecure` (bool) - Skip certificate verification (for testing/self-signed certs)
- `client_id` (str) - Custom client identifier

**Implementation:**
```python
# TLS/SSL configuration
if self.use_tls:
    import ssl
    if self.tls_insecure:
        # For testing or self-signed certificates
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)
    else:
        # Secure TLS with certificate verification
        self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

# Client ID support
if self.client_id:
    self.client = mqtt.Client(client_id=self.client_id)
else:
    self.client = mqtt.Client()
```

### 2. Environment Configuration (`.env.example`)

**New Variables:**
```bash
MQTT_USE_TLS=false           # Enable TLS/SSL (required for HiveMQ Cloud)
MQTT_TLS_INSECURE=false     # Skip certificate verification
MQTT_CLIENT_ID=              # Custom client identifier
```

**HiveMQ Cloud Example:**
```bash
MQTT_ENABLED=true
MQTT_BROKER=xxxxx.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
MQTT_USE_TLS=true
MQTT_TLS_INSECURE=false
MQTT_CLIENT_ID=meetrec_device_001
MQTT_TOPIC_PREFIX=meetrec/device1
```

### 3. Documentation (`README.md`)

**Added HiveMQ Cloud Setup Section:**
1. Account creation
2. Cluster setup
3. Credential management
4. Configuration example
5. Testing instructions

**Key Points:**
- Free tier: 100 connections, 10 GB data transfer/month
- Built-in TLS/SSL security
- Web-based MQTT client for testing
- Global availability
- No broker installation required

### 4. Example Client (`examples/mqtt_client_example.py`)

**Updated to Support Both:**
- Local MQTT brokers (Mosquitto)
- HiveMQ Cloud with TLS

**Configuration Options:**
```python
# For local broker:
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USE_TLS = False

# For HiveMQ Cloud:
MQTT_BROKER = "xxxxx.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USE_TLS = True
```

### 5. Workflow Documentation (`MQTT_WORKFLOW.md`)

**Added HiveMQ Cloud Section:**
- Benefits of using HiveMQ Cloud
- Complete configuration example
- Security considerations
- Comparison with self-hosted options

## Benefits of HiveMQ Cloud

1. **No Maintenance**: No broker installation or management
2. **Built-in Security**: TLS/SSL by default
3. **Scalability**: Automatic scaling based on usage
4. **Reliability**: High availability and global presence
5. **Free Tier**: Perfect for small deployments and testing
6. **Web Testing**: Built-in MQTT client for debugging

## Testing

Verified:
- ✅ TLS configuration parsing
- ✅ Client ID handling
- ✅ Backward compatibility (works without TLS)
- ✅ All existing tests pass
- ✅ CodeQL security scan: 0 vulnerabilities

## Migration Guide

### From Local Mosquitto to HiveMQ Cloud

1. Create HiveMQ Cloud account and cluster
2. Update `.env`:
   ```bash
   MQTT_BROKER=xxxxx.s1.eu.hivemq.cloud  # Change from localhost
   MQTT_PORT=8883                          # Change from 1883
   MQTT_USE_TLS=true                       # Add this line
   MQTT_USERNAME=your_username             # Add credentials
   MQTT_PASSWORD=your_password             # Add credentials
   ```
3. Restart application
4. Test with HiveMQ Cloud Web Client

### From Other Cloud Brokers

Most cloud MQTT brokers (AWS IoT Core, Azure IoT Hub, etc.) require TLS. The same configuration works:

```bash
MQTT_ENABLED=true
MQTT_BROKER=your-broker-url
MQTT_PORT=8883
MQTT_USE_TLS=true
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
```

## Troubleshooting

**Connection fails with TLS errors:**
- Ensure `MQTT_USE_TLS=true`
- Check broker URL is correct
- Verify port is 8883 (not 1883)

**Certificate verification errors:**
- For production: Ensure system CA certificates are up to date
- For testing only: Set `MQTT_TLS_INSECURE=true` (not recommended)

**Connection refused:**
- Verify username/password are correct
- Check firewall allows outbound connections to port 8883
- Confirm cluster is running in HiveMQ Cloud Console

## Commit

All changes in commit: `71a8bca` - "Add HiveMQ Cloud support with TLS/SSL configuration"
