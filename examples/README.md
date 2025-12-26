# Exempel

Denna katalog innehåller exempel på hur man använder mötesinspelaren.

## MQTT-klient exempel

`mqtt_client_example.py` - Interaktiv MQTT-klient för fjärrstyrning av inspelaren.

### Användning

```bash
# Installera paho-mqtt om det inte redan är installerat
pip install paho-mqtt

# Redigera mqtt_client_example.py och ändra MQTT-inställningar:
# MQTT_BROKER, MQTT_PORT, DEVICE_TOPIC_PREFIX

# Kör exempel
python3 examples/mqtt_client_example.py
```

### Funktioner

- Skicka kommandon (start, stop, test) till inspelaren
- Lyssna på status-uppdateringar från enheten
- Uppdatera konfiguration (rum, e-post, webhook)
- Interaktiv kommandoprompt

### Exempel på användning

```
> start           # Starta inspelning
> stop            # Stoppa och ladda upp
> test            # Testa ljudnivåer
> config          # Uppdatera konfiguration
> quit            # Avsluta
```

## JSON MQTT-kommandon med email och n8n

`JSON_MQTT_N8N_EXAMPLE.md` - Komplett guide för att använda JSON MQTT-kommandon med email-stöd.

### Funktioner

- Starta inspelningar med email-adress: `{"command": "start", "email": "user@example.com"}`
- Email skickas automatiskt till n8n webhook
- n8n kan använda email för att skicka transkriptioner/sammanfattningar
- Exempel på komplett n8n-workflow
- Home Assistant-integration
- Python-exempel
- Bakåtkompatibelt med textkommandon

## Testskript

### MQTT Command Test
`mqtt_command_test.py` - Testar grundläggande MQTT-kommandohantering.

```bash
python3 examples/mqtt_command_test.py
```

### JSON MQTT Command Test
`mqtt_json_command_test.py` - Testar JSON-kommandoformat och email-extraktion.

```bash
python3 examples/mqtt_json_command_test.py
```

Testar:
- JSON-parsning av kommandon
- Email-extraktion från JSON
- Bakåtkompatibilitet med textkommandon
- Olika JSON-format och edge cases

### Integration Test
`integration_test_email_flow.py` - Testar hela flödet från MQTT till upload.

```bash
python3 examples/integration_test_email_flow.py
```

Testar:
- MQTT JSON-kommando → Email-extraktion → GUI-lagring → Upload med email
- Verifierar att email kommer fram till upload-funktionen
- Testar bakåtkompatibilitet
