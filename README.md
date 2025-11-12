# meetrec-pi — Raspberry Pi mötesinspelare (Touch GUI) med Google Drive-upload

Enkel touch-baserad inspelare för Raspberry Pi + ReSpeaker (eller annan USB-mik) som:
- Startar och stoppar inspelning via en touchskärm (Tkinter-GUI)
- Visar nivåmätare i testläge (per kanal)
- Har **stor röd REC-indikator** + **centrerad timer** under inspelning
- Konverterar WAV → FLAC med ffmpeg
- Laddar upp filen till **Google Drive** (Service Account eller OAuth)
- (Valfritt) Stöd finns kvar för S3/HTTP om du vill växla senare

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
Kopiera `.env.example` → `.env` och fyll i värden. Minsta nödvändiga för **Google Drive**:

```bash
UPLOAD_TARGET="gdrive"
DRIVE_FOLDER_ID="xxxx_xxxxxxxxxxxxxxxxx"  # Mappens ID i Drive (syns i URL)
# Välj ETT auth-sätt:

# (A) Service Account (rekommenderas på Pi utan användare)
DRIVE_AUTH_TYPE="service_account"
DRIVE_SERVICE_ACCOUNT_JSON="/home/pi/meetrec/sa.json"  # sökväg till din SA-nyckel

# (B) OAuth (engångs-inloggning via terminal)
#DRIVE_AUTH_TYPE="oauth"
#DRIVE_CLIENT_SECRETS="/home/pi/meetrec/client_secret.json"
#DRIVE_TOKEN_PATH="/home/pi/meetrec/token.json"
```

> **Service Account**: Aktivera Drive API i Google Cloud, skapa Service Account + JSON-nyckel, **dela Drive-mappen** med SA-e-postadressen.  
> **OAuth**: Aktivera Drive API, skapa "Desktop app" OAuth client. Första körningen visar en URL som du följer i valfri webbläsare; klistra sedan in koden i terminalen (token sparas).

Läs in env i din shell-session:
```bash
set -a; source .env; set +a
```

## 4) Kör
```bash
source ~/meetrec/bin/activate
python src/meetrec_gui.py
```
- **Testa nivåer** visar VU-staplar (RMS) för `CHANNELS_TEST` kanaler.
- **Starta inspelning** skapar WAV (mono, 16 kHz), visar stor röd **REC** + timer.
- **Stoppa & ladda upp** konverterar till FLAC och laddar upp till Drive.
- Statusfältet visar resultat och en länk (webViewLink) om allt gick bra.

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

## 7) Vanliga justeringar
- **Välj ljudenhet**: sätt `ALSA_DEVICE = "hw:1,0"` i koden om flera ljudkort finns. Hitta ID med `arecord -l`.
- **Kanalantal i testläget**: justera `CHANNELS_TEST` (t.ex. 4 eller 6 för ReSpeaker v2.0).
- **Mono/FLAC**: transkriberingstjänster föredrar ofta mono 16 kHz. Du kan höja kvalitet, alternativt spara fler kanaler.

---

**Licens:** MIT
