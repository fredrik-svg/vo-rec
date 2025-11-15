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
