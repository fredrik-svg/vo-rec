# meetrec-pi — Raspberry Pi mötesinspelare (Touch GUI) med n8n-upload

Enkel touch-baserad inspelare för Raspberry Pi + ReSpeaker (eller annan USB-mik) som:
- Startar och stoppar inspelning via en touchskärm (Tkinter-GUI)
- Visar nivåmätare i testläge (per kanal)
- Har **stor röd REC-indikator** + **centrerad timer** under inspelning
- Konverterar WAV → FLAC med ffmpeg
- Laddar upp filen till **Google Drive** (Service Account eller OAuth)
- (Valfritt) Stöd finns kvar för S3/HTTP/n8n/MQTT om du vill växla senare

## 1) Förkrav (OS-paket)
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv ffmpeg
# Ljudverktyg är praktiska vid felsökning:
sudo apt install -y alsa-utils
# Tkinter ingår ofta, annars:
sudo apt install -y python3-tk
```

## 2) Skapa virtuell miljö och installera Python-beroenden
```bash
python3 -m venv ~/meetrec
source ~/meetrec/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Konfiguration (.env)
Kopiera `.env.example` → `.env` och fyll i värden.

### Konfiguration av n8n workflow (rekommenderad uppladdning)

**n8n** är ett workflow automation-verktyg som kan ta emot filer via webhooks. Detta är ett enkelt sätt att automatiskt bearbeta inspelningar:

1. **Skapa en n8n workflow** med en Webhook-nod
   - Sätt webhook-noden till att acceptera POST-förfrågningar
   - Konfigurera den att ta emot filer (multipart/form-data)
   - Filen kommer att skickas med fältnamnet "file"

2. **Kopiera webhook-URL:en** från n8n (visas i webhook-nodens inställningar)

3. **Konfigurera .env**:
   ```bash
   UPLOAD_TARGET="n8n"
   N8N_WEBHOOK_URL="https://your-n8n-instance.com/webhook/your-workflow-id"
   # Valfritt, om din webhook kräver autentisering:
   N8N_AUTH_HEADER="Bearer your-token-here"
   ```

4. **I din n8n workflow** kan du sedan:
   - Transkribera ljudet med en AI-tjänst
   - Spara filen till en molntjänst
   - Skicka notifikationer
   - Extrahera insikter och metadata

### Konfiguration av MQTT / HiveMQ Cloud (alternativ uppladdning)

**MQTT** är ett lättviktigt meddelandeprotokoll som är perfekt för IoT-enheter som Raspberry Pi. **HiveMQ Cloud** är en fullständigt hanterad MQTT-broker i molnet:

1. **Skapa ett HiveMQ Cloud-konto**
   - Gå till [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)
   - Skapa ett gratis konto och ett nytt cluster
   - Anteckna cluster-URL:en (t.ex. `xxxxxxxx.s1.eu.hivemq.cloud`)

2. **Skapa MQTT-autentiseringsuppgifter**
   - I HiveMQ Cloud Console, gå till "Access Management"
   - Skapa en ny användare med användarnamn och lösenord
   - Ge användaren publiceringsrättigheter för ditt topic

3. **Konfigurera .env**:
   ```bash
   UPLOAD_TARGET="mqtt"
   MQTT_BROKER="xxxxxxxx.s1.eu.hivemq.cloud"
   MQTT_PORT=8883
   MQTT_USERNAME="din-mqtt-användare"
   MQTT_PASSWORD="ditt-mqtt-lösenord"
   MQTT_TOPIC="recordings/meetings"
   MQTT_USE_TLS=true
   ```

4. **MQTT-meddelanden**
   - Inspelningar publiceras som JSON-meddelanden till det konfigurerade topic
   - Meddelandet innehåller filnamn, timestamp, storlek och filen kodad i base64
   - Du kan prenumerera på topic:et från andra system för att ta emot och bearbeta inspelningar

5. **Prenumerera på meddelanden** (exempel med mosquitto_sub):
   ```bash
   mosquitto_sub -h xxxxxxxx.s1.eu.hivemq.cloud -p 8883 \
     -u "din-mqtt-användare" -P "ditt-mqtt-lösenord" \
     -t "recordings/meetings" --capath /etc/ssl/certs/
   ```

Läs in env i din shell-session:
```bash
set -a; source .env; set +a
```

## 4) Kör
```bash
source ~/meetrec/bin/activate
python src/meetrec_gui.py
```
- **Testa nivåer** visar VU-staplar (RMS) för `CHANNELS_TEST` kanaler med realtidsvärden i procent och dB.
  - Varje kanal visar aktuell nivå både visuellt och numeriskt
  - Använd **Volymkontroll (Gain)**-reglaget för att justera ingående ljudnivå (0.1x - 5.0x)
  - Standardvärde är 1.0x (ingen förstärkning)
- **Starta inspelning** skapar WAV (mono, 16 kHz), visar stor röd **REC** + timer.
- **Stoppa & ladda upp** konverterar till FLAC och laddar upp till vald destination.
- Statusfältet visar resultat och status för uppladdningen.

## 5) Autostart (kiosk)
### Alternativ A: Desktop autostart
Kopiera `autostart/meetrec.desktop` till `~/.config/autostart/` och uppdatera sökvägarna i filen.

### Alternativ B: systemd-tjänst (om du kör utan grafiskt skrivbord)
Anpassa `service/meetrec.service` (stigarna) och installera:
```bash
sudo cp service/meetrec.service /etc/systemd/system/meetrec.service
sudo systemctl daemon-reload
sudo systemctl enable --now meetrec.service
systemctl status meetrec.service
```

## 6) GitHub – initiera repo och pusha
```bash
cd <mappen-där-du-packat-upp-zippen>
git init
git add .
git commit -m "Initial commit: meetrec-pi"
git branch -M main
git remote add origin git@github.com:<ditt-konto>/<ditt-repo>.git
git push -u origin main
```

## 7) MQTT-fjärrstyrning och konfiguration

Mötesinspelaren stöder MQTT-baserad fjärrstyrning och konfigurationshantering. Detta gör det möjligt att:
- Starta/stoppa inspelningar på distans
- Övervaka enhetens status
- Konfigurera parametrar som webhook, rum och e-post
- Hantera WiFi-inställningar

### Aktivera MQTT

Lägg till följande i `.env`:

```bash
# Aktivera MQTT-kontroll
MQTT_ENABLED=true

# MQTT Broker-inställningar
MQTT_BROKER=mqtt.example.com        # Din MQTT-broker
MQTT_PORT=1883                       # Port (1883 standard, 8883 för TLS)
MQTT_USERNAME=your_username          # Valfritt
MQTT_PASSWORD=your_password          # Valfritt
MQTT_TOPIC_PREFIX=meetrec/device1    # Unikt för varje enhet (normaliseras automatiskt)

**Notera:** Topic prefix normaliseras automatiskt för att undvika vanliga problem:
- Ledande och avslutande snedstreck tas bort
- Dubbla snedstreck ersätts med enkla
- Mellanslag tas bort
- Detta säkerställer kompatibilitet med HiveMQ Cloud och andra MQTT-brokers

# TLS/SSL (krävs för HiveMQ Cloud)
MQTT_USE_TLS=false                   # Sätt till true för krypterad anslutning
MQTT_TLS_INSECURE=false             # Hoppa över certifikatverifiering (ej rekommenderat)
MQTT_CLIENT_ID=                      # Valfritt client ID

# Enhetskonfiguration
DEVICE_ROOM=Konferensrum A           # Vilket rum enheten är i
DEVICE_EMAIL=recordings@example.com  # E-post för notifikationer
DEVICE_WEBHOOK_URL=https://...       # Webhook för anpassad hantering
```

### HiveMQ Cloud Setup

HiveMQ Cloud är en molnbaserad MQTT-broker som fungerar utmärkt med mötesinspelaren:

1. **Skapa konto på HiveMQ Cloud**
   - Gå till [https://www.hivemq.com/mqtt-cloud-broker/](https://www.hivemq.com/mqtt-cloud-broker/)
   - Skapa ett gratis konto (upp till 100 anslutningar)

2. **Skapa en cluster**
   - Logga in på HiveMQ Cloud Console
   - Skapa en ny cluster (välj region närmast dig)
   - Anteckna Cluster URL (t.ex. `xxxxx.s1.eu.hivemq.cloud`)

3. **Skapa användaruppgifter**
   - Under "Access Management" → "Credentials"
   - Skapa nytt användarnamn och lösenord
   - Spara uppgifterna säkert

4. **Konfigurera .env för HiveMQ Cloud**
   ```bash
   MQTT_ENABLED=true
   MQTT_BROKER=xxxxx.s1.eu.hivemq.cloud  # Din cluster URL
   MQTT_PORT=8883                          # HiveMQ Cloud använder TLS-port
   MQTT_USERNAME=your_hivemq_username      # Från steg 3
   MQTT_PASSWORD=your_hivemq_password      # Från steg 3
   MQTT_TOPIC_PREFIX=meetrec/device1
   MQTT_USE_TLS=true                       # MÅSTE vara true för HiveMQ Cloud
   MQTT_TLS_INSECURE=false                # Använd säker certifikatverifiering
   MQTT_CLIENT_ID=meetrec_device_001      # Valfritt men rekommenderat
   ```

5. **Testa anslutningen**
   - Använd HiveMQ Cloud Web Client (finns i konsolen) för att testa
   - Prenumerera på `meetrec/device1/#` för att se alla meddelanden
   - Testa kommandon genom att publicera till `meetrec/device1/command`


### MQTT Topics

Enheten använder följande topics (med prefix `meetrec/device1` som exempel):

**Kommandon (subscribe):**
- `meetrec/device1/command` - Skicka kommandon till enheten
  - `start` - Starta inspelning
  - `stop` - Stoppa inspelning och ladda upp
  - `test` - Starta/stoppa nivåtest

**Status (publish):**
- `meetrec/device1/status` - Enhetens aktuella status
  - `ready` - Redo för inspelning
  - `recording` - Inspelning pågår
  - `processing` - Konverterar inspelning
  - `converting` - Konverterar WAV→FLAC
  - `uploading` - Laddar upp
  - `error` - Fel uppstod

**Konfiguration:**
- `meetrec/device1/config` - Nuvarande konfiguration (publish)
- `meetrec/device1/config/set` - Uppdatera konfiguration (subscribe)

**Inspelningar:**
- `meetrec/device1/recording` - Information om färdiga inspelningar

### Konfigurera enheten via MQTT

Skicka ett JSON-meddelande till `meetrec/device1/config/set`:

```json
{
  "room": "Konferensrum B",
  "email": "ny-adress@example.com",
  "webhook_url": "https://webhook.site/your-id",
  "upload_target": "n8n",
  "n8n_webhook_url": "https://n8n.example.com/webhook/abc123"
}
```

**WiFi-konfiguration:**
```json
{
  "wifi_ssid": "DittWiFi",
  "wifi_password": "dittlösenord"
}
```

### Exempel med mosquitto_pub

```bash
# Starta inspelning
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/command" -m "start"

# Stoppa inspelning
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/command" -m "stop"

# Uppdatera rum
mosquitto_pub -h mqtt.example.com -t "meetrec/device1/config/set" -m '{"room":"Konferensrum C"}'

# Lyssna på status
mosquitto_sub -h mqtt.example.com -t "meetrec/device1/#"
```

### Home Assistant integration

Exempel på Home Assistant-konfiguration för att styra inspelaren:

```yaml
mqtt:
  button:
    - name: "Meetrec Start Recording"
      command_topic: "meetrec/device1/command"
      payload_press: "start"
    
    - name: "Meetrec Stop Recording"
      command_topic: "meetrec/device1/command"
      payload_press: "stop"
  
  sensor:
    - name: "Meetrec Status"
      state_topic: "meetrec/device1/status"
      value_template: "{{ value_json.status }}"
    
    - name: "Meetrec Room"
      state_topic: "meetrec/device1/config"
      value_template: "{{ value_json.room }}"
```

## 8) Vanliga justeringar
- **Välj ljudenhet**: sätt `ALSA_DEVICE=hw:1,0` i `.env` om flera ljudkort finns. Hitta ID med `arecord -l`.
- **Kanalantal i testläget**: justera `CHANNELS_TEST` (t.ex. 4 eller 6 för ReSpeaker v2.0).
  - Systemet öppnar automatiskt alla tillgängliga kanaler från enheten för att fånga alla mikrofoner
  - GUI:t visar de första `CHANNELS_TEST` kanalerna
  - För ReSpeaker 4-Mic Array v2.0 med 6 kanaler (4 mic + 2 ref), sätt `CHANNELS_TEST=4` för att visa de fyra mikrofonerna
- **Volymkontroll**: Använd Gain-reglaget i GUI:t för att justera mikrofonnivåer i realtid (0.1x - 5.0x). Om ljud är för svagt, öka gain; om staplarna klipps vid max, minska gain.
- **Multi-kanal inspelning**: Sätt `CHANNELS_RECORD=4` för att spela in med alla 4 mikrofoner på ReSpeaker. Kanalerna kombineras automatiskt till mono för bättre ljudkvalitet.

## 9) Ljudkvalitet och ElevenLabs-optimering

Inspelningar är optimerade för ElevenLabs voice cloning och annan AI-baserad talbearbetning.

### ElevenLabs-krav
ElevenLabs voice cloning kräver:
- **Format**: PCM S16LE (16-bit little-endian)
- **Sample rate**: 16 kHz (optimal för tal)
- **Kanaler**: Mono

Dessa inställningar är standard och används automatiskt.

### ReSpeaker 4-Mic Array
ReSpeaker 4-Mic Array har följande specifikationer:
- **Max sample rate**: 16 kHz (hårdvarubegränsning)
- **Kanaler**: 6 totalt (4 mikrofoner + 2 referenskanaler)
- **Mikrofoner**: Digital MEMS med 61 dB SNR
- **Inbyggd DSP**: AEC, brusreducering, de-reverb och beamforming

För bästa kvalitet med ReSpeaker, sätt `CHANNELS_RECORD=4` för att använda alla mikrofoner.

### Automatiska ljudförbättringar
När en inspelning konverteras från WAV till FLAC appliceras följande filter:

1. **Kanalmixning** - Om flera kanaler spelats in kombineras de till mono med lika vikt
2. **Högpassfilter (80 Hz)** - Tar bort lågfrekvent brus och rumsakustik (konfigurerbart med `HIGHPASS_FREQ`)
3. **Lågpassfilter (8 kHz)** - Tar bort högfrekvent brus (konfigurerbart med `LOWPASS_FREQ`)
4. **Brusreducering (afftdn)** - FFT-baserad brusreducering för renare tal (konfigurerbart med `ENABLE_NOISE_REDUCTION`)
5. **Volymförstärkning (Gain)** - Applicerar den gain-nivå du valt med Gain-reglaget i GUI:t
6. **EBU R128 Loudness-normalisering** - Optimerar ljudnivån till -16 LUFS (konfigurerbart med `LOUDNORM_TARGET`)

### Konfigurera ljudinställningar
Alla ljudinställningar kan konfigureras via miljövariabler i `.env`:

```bash
# Grundläggande inställningar
SAMPLE_RATE=16000           # Sample rate (16 kHz max för ReSpeaker)
AUDIO_FORMAT=S16_LE         # 16-bit PCM
CHANNELS_TEST=4             # Kanaler att visa i testläget
CHANNELS_RECORD=4           # Kanaler vid inspelning (1 eller 4)
ALSA_DEVICE=hw:1,0          # ReSpeaker-enhet

# Avancerade ljudfilter
HIGHPASS_FREQ=80            # Högpassfilter (Hz)
LOWPASS_FREQ=8000           # Lågpassfilter (Hz)
ENABLE_NOISE_REDUCTION=true # Aktivera brusreducering
LOUDNORM_TARGET=-16         # Målnivå i LUFS
```

### Tips för bättre ljudkvalitet
- **Låg ljudnivå**: Öka Gain-reglaget till 2.0x-3.0x innan inspelning. Loudness-normaliseringen höjer också nivån automatiskt.
- **Eko**: Högpassfiltret reducerar rumseko. För bästa resultat, placera mikrofonen nära talaren.
- **Brus**: Brusreducering är aktiverad som standard. Inaktivera med `ENABLE_NOISE_REDUCTION=false` om du vill ha originalljudet.
- **Multi-mikrofon**: Med `CHANNELS_RECORD=4` kombineras alla mikrofoner för bättre signal-brusförhållande.

---

**Licens:** MIT
