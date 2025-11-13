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

### Konfiguration av Service Account (rekommenderat för oövervakad drift)

**Service Account** är det enklaste alternativet för Raspberry Pi som kör utan användarinteraktion:

1. **Aktivera Drive API** i Google Cloud Console
2. **Skapa Service Account** + JSON-nyckel
3. **Dela Drive-mappen** med Service Account-e-postadressen (finns i JSON-filen)

### Konfiguration av OAuth (för användarbaserad autentisering)

**OAuth** kräver engångs-inloggning men ger åtkomst till din egen Google Drive. Följ dessa steg noggrant:

#### Steg 1: Skapa eller välj ett Google Cloud-projekt

1. Gå till [Google Cloud Console](https://console.cloud.google.com/)
2. Skapa ett nytt projekt eller välj ett befintligt projekt
   - Klicka på projektväljaren högst upp
   - Klicka på "Nytt projekt" (New Project)
   - Ge projektet ett namn (t.ex. "MeetRec Pi")
   - Klicka "Skapa" (Create)

#### Steg 2: Aktivera Google Drive API

1. I Google Cloud Console, gå till "API:er och tjänster" → "Bibliotek" (APIs & Services → Library)
2. Sök efter "Google Drive API"
3. Klicka på "Google Drive API" i resultaten
4. Klicka på knappen "Aktivera" (Enable)
5. Vänta tills API:et är aktiverat (kan ta några sekunder)

#### Steg 3: Konfigurera OAuth-medgivandeskärm (Consent Screen)

1. Gå till "API:er och tjänster" → "OAuth-medgivandeskärm" (OAuth consent screen)
2. Välj användartyp:
   - **Extern** (External): Om du vill använda ditt personliga Google-konto
   - **Internt** (Internal): Endast om du har Google Workspace och vill begränsa till din organisation
3. Klicka "Skapa" (Create)
4. Fyll i grundläggande information:
   - **Appnamn**: t.ex. "MeetRec Pi Recorder"
   - **E-post för användarsupport**: din e-postadress
   - **E-post för utvecklarkontakt**: din e-postadress
5. Klicka "Spara och fortsätt" (Save and Continue)
6. På sidan "Omfång" (Scopes):
   - Du behöver inte lägga till några omfång här (hanteras av applikationen)
   - Klicka "Spara och fortsätt"
7. På sidan "Testanvändare" (Test users):
   - Klicka "Lägg till användare" (Add Users)
   - Lägg till din egen e-postadress (det Google-konto du vill använda)
   - Klicka "Spara och fortsätt"
8. Granska sammanfattningen och klicka "Tillbaka till instrumentpanelen" (Back to Dashboard)

#### Steg 4: Skapa OAuth 2.0-klientinformation

1. Gå till "API:er och tjänster" → "Autentiseringsuppgifter" (Credentials)
2. Klicka på "+ Skapa autentiseringsuppgifter" (Create Credentials) högst upp
3. Välj "OAuth-klient-ID" (OAuth client ID)
4. Välj programtyp: **Datorprogram** (Desktop app)
5. Ge den ett namn, t.ex. "MeetRec Desktop Client"
6. Klicka "Skapa" (Create)
7. En dialogruta visas med klient-ID och klienthemlighet
   - Klicka "Ladda ned JSON" (Download JSON)
   - Spara filen som `client_secret.json`

#### Steg 5: Placera client_secret.json på din Raspberry Pi

1. Kopiera `client_secret.json` till din Raspberry Pi:
   ```bash
   # Från din dator (om du använder scp):
   scp client_secret.json pi@<pi-ip-adress>:~/meetrec/client_secret.json
   
   # Eller kopiera manuellt via USB-sticka eller annan metod
   ```

2. Se till att sökvägen i `.env` matchar:
   ```bash
   DRIVE_CLIENT_SECRETS="/home/pi/meetrec/client_secret.json"
   DRIVE_TOKEN_PATH="/home/pi/meetrec/token.json"
   ```

#### Steg 6: Genomför första autentiseringen

1. Första gången du kör applikationen med OAuth-konfiguration kommer en autentiseringsprocess att startas:
   ```bash
   source ~/meetrec/bin/activate
   python src/meetrec_gui.py
   ```

2. Terminalen visar en URL som ser ut ungefär så här:
   ```
   Please visit this URL to authorize this application:
   https://accounts.google.com/o/oauth2/auth?client_id=...
   ```

3. **Öppna URL:en i en webbläsare** (kan göras på vilken enhet som helst):
   - Logga in med det Google-konto du lade till som testanvändare
   - Google visar en varning om att appen inte är verifierad:
     - Klicka "Avancerat" (Advanced)
     - Klicka "Gå till [Appnamn] (osäkert)" (Go to [App name] (unsafe))
   - Godkänn åtkomst till Google Drive
   - Du får en auktoriseringskod som visas i webbläsaren

4. **Kopiera auktoriseringskoden** och klistra in den i terminalen där applikationen väntar

5. Token sparas automatiskt i filen som anges av `DRIVE_TOKEN_PATH`

6. Framtida körningar använder den sparade token och kräver ingen ny inloggning (såvida inte token upphör eller återkallas)

#### Felsökning OAuth

- **"Appen har blockerats"**: Se till att du har lagt till ditt Google-konto som testanvändare i steg 3.7
- **Token har upphört**: Ta bort `token.json` och kör autentiseringsprocessen igen
- **Felaktig client_secret.json**: Kontrollera att filen är korrekt nedladdad och inte är tom eller korrupt
- **Nätverksfel**: Se till att Raspberry Pi har internetåtkomst för att nå Google-servrar

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
  - Systemet öppnar automatiskt alla tillgängliga kanaler från enheten för att fånga alla mikrofoner
  - GUI:t visar de första `CHANNELS_TEST` kanalerna
  - För ReSpeaker 4-Mic Array v2.0 med 6 kanaler (4 mic + 2 ref), sätt `CHANNELS_TEST=4` för att visa de fyra mikrofonerna
- **Volymkontroll**: Använd Gain-reglaget i GUI:t för att justera mikrofonnivåer i realtid (0.1x - 5.0x). Om ljud är för svagt, öka gain; om staplarna klipps vid max, minska gain.
- **Mono/FLAC**: transkriberingstjänster föredrar ofta mono 16 kHz. Du kan höja kvalitet, alternativt spara fler kanaler.

---

**Licens:** MIT
