#!/usr/bin/env python3
"""
Konfigurationshantering för mötesinspelaren.

Hanterar:
- Lagring och laddning av konfiguration
- Uppdatering av konfigurationsparametrar
- WiFi-inställningar (säker lagring)
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Hanterar konfiguration för mötesinspelaren"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initiera konfigurationshanterare.
        
        Args:
            config_path: Sökväg till konfigurationsfil (default: ~/.meetrec/config.json)
        """
        if config_path is None:
            config_path = Path.home() / ".meetrec" / "config.json"
        
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ladda konfiguration från fil eller skapa standardkonfiguration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Ladda konfiguration från fil eller skapa standardkonfiguration.
        
        Returns:
            Dictionary med konfiguration
        """
        # Standardkonfiguration från miljövariabler
        default_config = {
            "room": os.getenv("DEVICE_ROOM", ""),
            "email": os.getenv("DEVICE_EMAIL", ""),
            "webhook_url": os.getenv("DEVICE_WEBHOOK_URL", ""),
            "upload_target": os.getenv("UPLOAD_TARGET", "n8n"),
            "n8n_webhook_url": os.getenv("N8N_WEBHOOK_URL", ""),
        }
        
        # Försök ladda från fil
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                # Sammanfoga med standardvärden (laddat tar prioritet)
                default_config.update(loaded_config)
                logger.info(f"Konfiguration laddad från {self.config_path}")
            except Exception as e:
                logger.warning(f"Kunde inte ladda konfiguration från {self.config_path}: {e}")
        
        return default_config
    
    def save_config(self) -> bool:
        """
        Spara nuvarande konfiguration till fil.
        
        Returns:
            True om lyckades, False annars
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Konfiguration sparad till {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Kunde inte spara konfiguration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Hämta konfigurationsvärde.
        
        Args:
            key: Nyckel för värdet
            default: Standardvärde om nyckeln inte finns
            
        Returns:
            Konfigurationsvärde
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Sätt konfigurationsvärde och spara.
        
        Args:
            key: Nyckel för värdet
            value: Värde att sätta
            
        Returns:
            True om lyckades, False annars
        """
        self.config[key] = value
        return self.save_config()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Uppdatera flera konfigurationsvärden samtidigt.
        
        Args:
            updates: Dictionary med uppdateringar
            
        Returns:
            True om lyckades, False annars
        """
        self.config.update(updates)
        return self.save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """
        Hämta all konfiguration (exkl. känsliga uppgifter som WiFi-lösenord).
        
        Returns:
            Dictionary med all konfiguration
        """
        # Skapa en kopia och filtrera bort känsliga uppgifter
        safe_config = self.config.copy()
        # Ta bort WiFi-lösenord om det finns
        if "wifi_password" in safe_config:
            safe_config["wifi_password"] = "***"
        return safe_config
    
    def set_wifi_credentials(self, ssid: str, password: str) -> bool:
        """
        Sätt WiFi-autentiseringsuppgifter (lagras separat för säkerhet).
        
        Args:
            ssid: WiFi SSID
            password: WiFi-lösenord
            
        Returns:
            True om lyckades, False annars
        """
        # Lagra WiFi-uppgifter i separat säker fil
        wifi_config_path = self.config_path.parent / "wifi_credentials.json"
        
        try:
            wifi_config = {
                "ssid": ssid,
                "password": password
            }
            with open(wifi_config_path, 'w') as f:
                json.dump(wifi_config, f, indent=2)
            
            # Sätt restriktiva filrättigheter (endast läsbar av ägare)
            wifi_config_path.chmod(0o600)
            
            logger.info(f"WiFi-uppgifter sparade för SSID: {ssid}")
            return True
        except Exception as e:
            logger.error(f"Kunde inte spara WiFi-uppgifter: {e}")
            return False
    
    def get_wifi_credentials(self) -> Optional[Dict[str, str]]:
        """
        Hämta WiFi-autentiseringsuppgifter.
        
        Returns:
            Dictionary med ssid och password, eller None om inte finns
        """
        wifi_config_path = self.config_path.parent / "wifi_credentials.json"
        
        if not wifi_config_path.exists():
            return None
        
        try:
            with open(wifi_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Kunde inte läsa WiFi-uppgifter: {e}")
            return None
