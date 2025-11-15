#!/usr/bin/env python3
"""
MQTT Client för fjärrstyrning av mötesinspelaren.

Tillhandahåller:
- Kommandomottagning via MQTT (start, stop, test levels)
- Statuspublicering
- Konfigurationshantering via MQTT
"""
import os
import json
import logging
from typing import Callable, Optional, Dict, Any
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT-klient för fjärrstyrning av mötesinspelaren"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initiera MQTT-klient med konfiguration.
        
        Args:
            config: Dictionary med MQTT-konfiguration
        """
        if not MQTT_AVAILABLE:
            raise RuntimeError("paho-mqtt är inte installerat. Installera med: pip install paho-mqtt")
        
        self.enabled = config.get("enabled", False)
        if not self.enabled:
            return
            
        self.broker = config.get("broker", "localhost")
        self.port = int(config.get("port", 1883))
        self.username = config.get("username")
        self.password = config.get("password")
        self.topic_prefix = config.get("topic_prefix", "meetrec/device")
        
        # MQTT topics
        self.topic_command = f"{self.topic_prefix}/command"
        self.topic_status = f"{self.topic_prefix}/status"
        self.topic_config = f"{self.topic_prefix}/config"
        self.topic_config_set = f"{self.topic_prefix}/config/set"
        self.topic_recording = f"{self.topic_prefix}/recording"
        
        # Callbacks
        self.on_start_callback: Optional[Callable] = None
        self.on_stop_callback: Optional[Callable] = None
        self.on_test_callback: Optional[Callable] = None
        self.on_config_update_callback: Optional[Callable[[Dict], None]] = None
        
        # Client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.connected = False
        
    def connect(self):
        """Anslut till MQTT-broker"""
        if not self.enabled:
            logger.info("MQTT är inte aktiverat")
            return
            
        try:
            logger.info(f"Ansluter till MQTT-broker {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Kunde inte ansluta till MQTT-broker: {e}")
            raise
    
    def disconnect(self):
        """Koppla från MQTT-broker"""
        if self.enabled:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback när anslutning till broker upprättas"""
        if rc == 0:
            logger.info("Ansluten till MQTT-broker")
            self.connected = True
            # Prenumerera på kommandotopics
            client.subscribe(self.topic_command)
            client.subscribe(self.topic_config_set)
            # Publicera initial status
            self.publish_status("ready")
        else:
            logger.error(f"Anslutning till MQTT-broker misslyckades med kod {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback när anslutningen bryts"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Oväntad frånkoppling från MQTT-broker: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback när meddelande tas emot"""
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        logger.debug(f"MQTT meddelande mottaget: {topic} = {payload}")
        
        try:
            if topic == self.topic_command:
                self._handle_command(payload)
            elif topic == self.topic_config_set:
                self._handle_config_set(payload)
        except Exception as e:
            logger.error(f"Fel vid hantering av MQTT-meddelande: {e}")
    
    def _handle_command(self, payload: str):
        """Hantera kommando från MQTT"""
        command = payload.lower().strip()
        
        if command == "start":
            logger.info("MQTT kommando: Start inspelning")
            if self.on_start_callback:
                self.on_start_callback()
        elif command == "stop":
            logger.info("MQTT kommando: Stoppa inspelning")
            if self.on_stop_callback:
                self.on_stop_callback()
        elif command == "test":
            logger.info("MQTT kommando: Testa nivåer")
            if self.on_test_callback:
                self.on_test_callback()
        else:
            logger.warning(f"Okänt MQTT kommando: {command}")
    
    def _handle_config_set(self, payload: str):
        """Hantera konfigurationsuppdatering från MQTT"""
        try:
            config = json.loads(payload)
            logger.info(f"MQTT konfigurationsuppdatering: {config}")
            if self.on_config_update_callback:
                self.on_config_update_callback(config)
        except json.JSONDecodeError as e:
            logger.error(f"Ogiltig JSON i config/set: {e}")
    
    def publish_status(self, status: str, extra_data: Optional[Dict] = None):
        """
        Publicera enhetsstatus till MQTT.
        
        Args:
            status: Statustext (t.ex. "ready", "recording", "uploading")
            extra_data: Extra data att inkludera i statusmeddelandet
        """
        if not self.enabled or not self.connected:
            return
            
        data = {"status": status}
        if extra_data:
            data.update(extra_data)
        
        payload = json.dumps(data)
        self.client.publish(self.topic_status, payload, retain=True)
    
    def publish_recording_complete(self, filename: str, upload_result: str):
        """
        Publicera information om färdig inspelning.
        
        Args:
            filename: Namn på inspelad fil
            upload_result: Resultat från uppladdning
        """
        if not self.enabled or not self.connected:
            return
        
        data = {
            "filename": filename,
            "upload_result": upload_result,
            "timestamp": None  # Kan läggas till om behövs
        }
        payload = json.dumps(data)
        self.client.publish(self.topic_recording, payload)
    
    def publish_config(self, config: Dict[str, Any]):
        """
        Publicera nuvarande konfiguration.
        
        Args:
            config: Dictionary med konfigurationsparametrar
        """
        if not self.enabled or not self.connected:
            return
        
        payload = json.dumps(config)
        self.client.publish(self.topic_config, payload, retain=True)
    
    def set_callbacks(self, 
                     on_start: Optional[Callable] = None,
                     on_stop: Optional[Callable] = None, 
                     on_test: Optional[Callable] = None,
                     on_config_update: Optional[Callable[[Dict], None]] = None):
        """
        Sätt callback-funktioner för kommandohantering.
        
        Args:
            on_start: Funktion att anropa vid start-kommando
            on_stop: Funktion att anropa vid stopp-kommando
            on_test: Funktion att anropa vid test-kommando
            on_config_update: Funktion att anropa vid konfigurationsuppdatering
        """
        if on_start:
            self.on_start_callback = on_start
        if on_stop:
            self.on_stop_callback = on_stop
        if on_test:
            self.on_test_callback = on_test
        if on_config_update:
            self.on_config_update_callback = on_config_update


def get_mqtt_config_from_env() -> Dict[str, Any]:
    """
    Läs MQTT-konfiguration från miljövariabler.
    
    Returns:
        Dictionary med MQTT-konfiguration
    """
    return {
        "enabled": os.getenv("MQTT_ENABLED", "false").lower() in ("true", "1", "yes"),
        "broker": os.getenv("MQTT_BROKER", "localhost"),
        "port": int(os.getenv("MQTT_PORT", "1883")),
        "username": os.getenv("MQTT_USERNAME"),
        "password": os.getenv("MQTT_PASSWORD"),
        "topic_prefix": os.getenv("MQTT_TOPIC_PREFIX", "meetrec/device"),
    }
