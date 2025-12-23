# JSON MQTT Command Format Implementation Summary

## Overview
This implementation adds support for JSON-formatted MQTT commands that include an email address. The email is passed through to the n8n webhook, allowing for automated user-specific notifications and transcription delivery.

## Changes Made

### 1. MQTT Client (`src/mqtt_client.py`)
**Changes:**
- Modified `_handle_command()` to parse both JSON and plain text commands
- Extract `command` and `email` fields from JSON payload
- Pass email as a keyword argument to the start callback
- Maintain full backward compatibility with plain text commands

**JSON Format:**
```json
{"command": "start", "email": "anna@example.com"}
{"command": "stop"}
```

**Text Format (backward compatible):**
```
start
stop
test
```

### 2. GUI Application (`src/meetrec_gui.py`)
**Changes:**
- Added `current_email` instance variable to store email during recording
- Updated `mqtt_on_start()` callback to accept optional email parameter
- Modified `_convert_and_upload()` to retrieve and pass email to upload function
- Updated `upload_file()` signature to accept email and room parameters
- Modified n8n upload section to send metadata as form data

**n8n Webhook Payload:**
```
file: [FLAC audio file]
filename: "meeting-20251223.flac"
email: "anna@example.com"
room: "badhuset"
```

### 3. Documentation Updates

#### MQTT_WORKFLOW.md
- Added JSON command format documentation
- Updated command table to show both JSON and text formats
- Added n8n webhook integration section with example workflow
- Updated Home Assistant examples to use JSON format

#### README.md
- Documented JSON command format in MQTT topics section
- Added n8n webhook integration documentation
- Updated mosquitto_pub examples to show JSON format
- Added usage examples for both formats

### 4. Test Suite

#### mqtt_json_command_test.py (New)
Tests JSON command parsing:
- JSON command with email
- JSON command without email
- Backward compatibility with plain text
- Various JSON formats and edge cases
- Invalid JSON fallback behavior
- **Result:** 5/5 tests passing

#### integration_test_email_flow.py (New)
Tests end-to-end flow:
- MQTT JSON command → Email extraction
- Email storage in GUI
- Email passed to upload function
- Backward compatibility (no email)
- **Result:** All checks passing

#### Existing Tests
- All 5 existing MQTT tests continue to pass
- No breaking changes to existing functionality

### 5. Examples and Documentation

#### JSON_MQTT_N8N_EXAMPLE.md (New)
Comprehensive guide including:
- MQTT command examples (JSON and text)
- Complete n8n workflow setup
- Home Assistant automation examples
- Python code example
- Troubleshooting guide
- Testing instructions

#### examples/README.md (Updated)
- Added documentation for new examples
- Added test suite descriptions
- Updated with JSON command information

## Test Results

### All Tests Passing ✅
```
MQTT Command Test:      5/5 tests passed
JSON Command Test:      5/5 tests passed
Integration Test:       All checks passed
Python Syntax Check:    All files compile successfully
```

## Backward Compatibility ✅

**Plain text commands still work:**
```bash
mosquitto_pub -t "meetrec/device1/command" -m "start"
mosquitto_pub -t "meetrec/device1/command" -m "stop"
```

**Existing behavior preserved:**
- All existing tests pass without modification
- Plain text commands function identically to before
- No changes required to existing MQTT clients
- Can be deployed without updating other systems

## Usage Examples

### MQTT with JSON (new feature)
```bash
# Start with email
mosquitto_pub -t "meetrec/device1/command" \
  -m '{"command": "start", "email": "anna@example.com"}'

# Stop
mosquitto_pub -t "meetrec/device1/command" \
  -m '{"command": "stop"}'
```

### MQTT with plain text (backward compatible)
```bash
mosquitto_pub -t "meetrec/device1/command" -m "start"
mosquitto_pub -t "meetrec/device1/command" -m "stop"
```

### n8n Workflow
The webhook receives:
- `file`: Binary FLAC audio
- `filename`: "meeting-20251223.flac"
- `email`: "anna@example.com" (if provided)
- `room`: "Konferensrum A" (from config)

## Security Considerations

- Email addresses are not validated (assumed to come from trusted sources)
- MQTT should use TLS (port 8883) for production
- n8n webhook should require authentication (N8N_AUTH_HEADER)
- Email is cleared from memory after upload

## Files Modified/Created

### Modified
1. `src/mqtt_client.py` - JSON parsing and email handling
2. `src/meetrec_gui.py` - Email storage and n8n payload
3. `MQTT_WORKFLOW.md` - Documentation updates
4. `README.md` - Usage examples and integration guide
5. `examples/README.md` - Example documentation

### Created
1. `examples/mqtt_json_command_test.py` - JSON command test suite
2. `examples/integration_test_email_flow.py` - Integration test
3. `examples/JSON_MQTT_N8N_EXAMPLE.md` - Comprehensive guide
4. `IMPLEMENTATION_CHANGES.md` - This file

## Deployment Notes

1. **No breaking changes** - Can be deployed without updating MQTT clients
2. **Backward compatible** - Existing plain text commands continue to work
3. **No database/config changes** - Uses existing configuration system
4. **Optional feature** - Email is optional, system works without it
5. **Tested** - All existing tests pass plus new tests for JSON feature

## Next Steps (Optional Enhancements)

1. Add email validation in MQTT client
2. Support multiple email recipients (comma-separated)
3. Add email to status messages for tracking
4. Store email in recording metadata
5. Add email to MQTT recording completion message
6. Support email in configuration updates (DEVICE_EMAIL fallback)

## Troubleshooting

### Email not received in n8n
1. Check MQTT logs for "Email extraherad från kommando"
2. Check GUI logs for "Skickar email till n8n"
3. Verify n8n webhook is receiving the email field
4. Check n8n execution logs

### JSON parsing errors
1. Ensure JSON is valid (use JSON validator)
2. Check MQTT logs for parsing errors
3. System will fallback to text parsing if JSON is invalid

### Testing
Run all tests:
```bash
python3 examples/mqtt_command_test.py
python3 examples/mqtt_json_command_test.py
python3 examples/integration_test_email_flow.py
```
