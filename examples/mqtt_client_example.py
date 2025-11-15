#!/usr/bin/env python3
"""
Exempel på MQTT-klientanvändning för fjärrstyrning av mötesinspelaren.

Detta exempel visar:
1. Hur man skickar kommandon till inspelaren
2. Hur man lyssnar på status-uppdateringar
3. Hur man uppdaterar konfiguration

Fungerar med både lokala MQTT-brokers och HiveMQ Cloud.
"""
import paho.mqtt.client as mqtt
import json
import time
import sys
import ssl

# MQTT-konfiguration (ändra efter behov)
# För lokal broker:
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USE_TLS = False

# För HiveMQ Cloud (kommentera ut ovan och använd dessa):
# MQTT_BROKER = "xxxxx.s1.eu.hivemq.cloud"  # Din HiveMQ Cloud URL
# MQTT_PORT = 8883
# MQTT_USE_TLS = True

MQTT_USERNAME = None  # Sätt om broker kräver autentisering (KRÄVS för HiveMQ Cloud)
MQTT_PASSWORD = None
DEVICE_TOPIC_PREFIX = "meetrec/device1"  # Ändra till din enhets topic prefix

def on_connect(client, userdata, flags, rc):
    """Callback när anslutning upprättas"""
    if rc == 0:
        print(f"✓ Ansluten till MQTT-broker {MQTT_BROKER}")
        # Prenumerera på alla topics från enheten
        client.subscribe(f"{DEVICE_TOPIC_PREFIX}/#")
        print(f"✓ Prenumererar på {DEVICE_TOPIC_PREFIX}/#")
    else:
        print(f"✗ Anslutning misslyckades med kod {rc}")

def on_message(client, userdata, msg):
    """Callback när meddelande tas emot"""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    print(f"\n📨 Meddelande från enhet:")
    print(f"   Topic: {topic}")
    
    # Försök parsa som JSON
    try:
        data = json.loads(payload)
        print(f"   Data: {json.dumps(data, indent=2)}")
    except:
        print(f"   Data: {payload}")

def send_command(client, command):
    """Skicka kommando till enheten"""
    topic = f"{DEVICE_TOPIC_PREFIX}/command"
    print(f"\n📤 Skickar kommando: {command}")
    client.publish(topic, command)
    print(f"   Till topic: {topic}")

def update_config(client, config_updates):
    """Uppdatera enhetskonfiguration"""
    topic = f"{DEVICE_TOPIC_PREFIX}/config/set"
    payload = json.dumps(config_updates)
    print(f"\n⚙️  Uppdaterar konfiguration:")
    print(f"   {json.dumps(config_updates, indent=2)}")
    client.publish(topic, payload)
    print(f"   Till topic: {topic}")

def main():
    """Huvudfunktion"""
    print("="*60)
    print("MQTT-klient för fjärrstyrning av mötesinspelaren")
    print("="*60)
    
    # Skapa MQTT-klient
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Konfigurera TLS för HiveMQ Cloud eller andra säkra brokers
    if MQTT_USE_TLS:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        print("✓ TLS/SSL aktiverad")
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Anslut
    try:
        print(f"\n🔌 Ansluter till {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"✗ Kunde inte ansluta till MQTT-broker: {e}")
        print(f"\nTips: Kontrollera att MQTT-brokern körs:")
        print(f"  - Lokal broker: sudo systemctl status mosquitto")
        print(f"  - HiveMQ Cloud: kontrollera URL, port (8883), användarnamn/lösenord")
        print(f"  - TLS: sätt MQTT_USE_TLS = True för HiveMQ Cloud")
        print(f"  - Test broker: använd MQTT_BROKER = 'test.mosquitto.org'")
        return 1
    
    # Starta loop i bakgrunden
    client.loop_start()
    
    # Vänta lite för att anslutningen ska upprättas
    time.sleep(2)
    
    print("\n" + "="*60)
    print("Interaktiv MQTT-klient - Kommandon:")
    print("="*60)
    print("  start    - Starta inspelning")
    print("  stop     - Stoppa inspelning och ladda upp")
    print("  test     - Testa ljudnivåer")
    print("  config   - Uppdatera konfiguration")
    print("  quit     - Avsluta")
    print("="*60)
    
    try:
        while True:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "quit":
                break
            elif cmd == "start":
                send_command(client, "start")
            elif cmd == "stop":
                send_command(client, "stop")
            elif cmd == "test":
                send_command(client, "test")
            elif cmd == "config":
                print("\nExempel på konfigurationsuppdateringar:")
                print("1. Ändra rum")
                print("2. Ändra e-post")
                print("3. Ändra webhook URL")
                print("4. Anpassad JSON")
                
                choice = input("Välj (1-4): ").strip()
                
                if choice == "1":
                    room = input("Ange rum: ")
                    update_config(client, {"room": room})
                elif choice == "2":
                    email = input("Ange e-post: ")
                    update_config(client, {"email": email})
                elif choice == "3":
                    webhook = input("Ange webhook URL: ")
                    update_config(client, {"webhook_url": webhook})
                elif choice == "4":
                    json_str = input("Ange JSON: ")
                    try:
                        config = json.loads(json_str)
                        update_config(client, config)
                    except json.JSONDecodeError as e:
                        print(f"✗ Ogiltig JSON: {e}")
            elif cmd:
                print(f"✗ Okänt kommando: {cmd}")
    
    except KeyboardInterrupt:
        print("\n\n⏹ Avbryter...")
    
    finally:
        print("👋 Kopplar från MQTT-broker...")
        client.loop_stop()
        client.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
