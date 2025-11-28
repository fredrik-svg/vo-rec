#!/usr/bin/env python3
import os, sys, time, subprocess, threading, queue, logging
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import ttk

import numpy as np
import sounddevice as sd

# Import MQTT och konfigurationshantering
try:
    from mqtt_client import MQTTClient, get_mqtt_config_from_env
    from config_manager import ConfigManager
    MQTT_SUPPORT = True
except ImportError as e:
    MQTT_SUPPORT = False
    logging.warning(f"MQTT-stöd ej tillgängligt: {e}")

# Konfigurera logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# ========= Konfig =========
AUDIO_DIR     = Path.home() / "meet_recordings"
AUDIO_DIR.mkdir(exist_ok=True)

SAMPLE_RATE   = 16000         # Räcker fint för tal
FORMAT        = "S16_LE"      # 16-bit PCM
CHANNELS_TEST = 4             # Antal kanaler att visa i "Testa nivåer" (ändra vid behov)
ALSA_DEVICE   = None          # None => standard. Eller t.ex. "hw:1,0" för ReSpeaker
MAX_HOURS     = 8

# Uppladdning (miljövariabler)
UPLOAD_TARGET = os.getenv("UPLOAD_TARGET", "n8n").lower()
AWS_REGION    = os.getenv("AWS_REGION", "eu-north-1")
S3_BUCKET     = os.getenv("S3_BUCKET")
S3_ENDPOINT   = os.getenv("S3_ENDPOINT_URL")
HTTP_UPLOAD_URL   = os.getenv("HTTP_UPLOAD_URL")
HTTP_AUTH_HEADER  = os.getenv("HTTP_AUTH_HEADER")
N8N_WEBHOOK_URL   = os.getenv("N8N_WEBHOOK_URL")
N8N_AUTH_HEADER   = os.getenv("N8N_AUTH_HEADER")

# ========= Hjälp =========
def ts_name():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def human_duration(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def wav_to_flac(wav_path: Path, gain: float = 1.0):
    """
    Konvertera WAV till FLAC med ljudförbättringar.
    
    Ljudförbättringar:
    - Högpassfilter (150 Hz) för att reducera eko och lågfrekvent brus
    - Volymförstärkning baserat på gain-parameter
    - Ljudnormalisering för att optimera ljudnivån
    
    Args:
        wav_path: Sökväg till WAV-filen
        gain: Volymförstärkning (1.0 = normal, 2.0 = dubbel, etc.)
    
    Returns:
        Tuple med (ok, flac_path, meddelande)
    """
    flac_path = wav_path.with_suffix(".flac")
    
    # Bygg ffmpeg-filter för ljudförbättring
    audio_filters = []
    
    # Högpassfilter för att reducera eko och lågfrekvent brus (150 Hz cutoff)
    # Detta hjälper till att ta bort rumsakustik och eko
    audio_filters.append("highpass=f=150")
    
    # Volymförstärkning om gain != 1.0
    if gain != 1.0:
        audio_filters.append(f"volume={gain}")
    
    # Normalisering för att optimera ljudnivån utan klippning
    # loudnorm är en standardbaserad ljudnormalisering (EBU R128)
    # I=-16: Målnivå för integrerad ljudstyrka (-16 LUFS, bra för tal)
    # TP=-1.5: True Peak max nivå (-1.5 dB, förhindrar klippning)
    # LRA=11: Loudness Range (11 LU, lämpligt för talat innehåll)
    audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    
    filter_chain = ",".join(audio_filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(wav_path),
        "-af", filter_chain,
        "-compression_level", "5",
        str(flac_path)
    ]
    
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return False, None, "Konvertering WAV->FLAC misslyckades"
    # Verifiera att FLAC-filen faktiskt skapades
    if not flac_path.exists():
        return False, None, f"FLAC-filen skapades inte: {flac_path}"
    if flac_path.stat().st_size == 0:
        return False, None, f"FLAC-filen är tom: {flac_path}"
    return True, flac_path, "ok"

def upload_file(flac_path: Path):
    # Verifiera att filen existerar innan upload (gäller alla metoder)
    if not flac_path.exists():
        return False, f"Uppladdningsfel: Filen finns inte: {flac_path}"
    if flac_path.stat().st_size == 0:
        return False, f"Uppladdningsfel: Filen är tom: {flac_path}"
    
    if UPLOAD_TARGET == "s3":
        try:
            import boto3
            session = boto3.session.Session(region_name=AWS_REGION)
            if S3_ENDPOINT:
                s3 = session.client("s3", endpoint_url=S3_ENDPOINT)
            else:
                s3 = session.client("s3")
            key = f"meetings/{flac_path.name}"
            s3.upload_file(str(flac_path), S3_BUCKET, key)
            return True, f"s3://{S3_BUCKET}/{key}"
        except Exception as e:
            return False, f"S3-fel: {e}"

    elif UPLOAD_TARGET == "http":
        try:
            import requests
            headers = {}
            if HTTP_AUTH_HEADER:
                headers["Authorization"] = HTTP_AUTH_HEADER
            with open(flac_path, "rb") as f:
                r = requests.post(HTTP_UPLOAD_URL, files={"file": (flac_path.name, f, "audio/flac")}, headers=headers, timeout=180)
            if r.status_code // 100 == 2:
                return True, f"HTTP {r.status_code}"
            else:
                return False, f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return False, f"HTTP-fel: {e}"

    elif UPLOAD_TARGET == "n8n":
        try:
            if not N8N_WEBHOOK_URL:
                return False, "N8N_WEBHOOK_URL saknas"
            import requests
            headers = {}
            if N8N_AUTH_HEADER:
                headers["Authorization"] = N8N_AUTH_HEADER
            with open(flac_path, "rb") as f:
                files = {"file": (flac_path.name, f, "audio/flac")}
                r = requests.post(N8N_WEBHOOK_URL, files=files, headers=headers, timeout=180)
            if r.status_code // 100 == 2:
                return True, f"n8n webhook {r.status_code} → {flac_path.name}"
            else:
                return False, f"n8n webhook {r.status_code}: {r.text[:200]}"
        except Exception as e:
            return False, f"n8n-fel: {e}"
    else:
        return False, f"Okänt UPLOAD_TARGET: {UPLOAD_TARGET}"

# ========= Ljudnivåmätning (Testläge) =========
class LevelMeter:
    def __init__(self, canvas: tk.Canvas, num_channels=4, samplerate=SAMPLE_RATE, device=ALSA_DEVICE, gain=1.0):
        self.canvas = canvas
        self.w = int(canvas["width"])
        self.h = int(canvas["height"])
        self.bars = []
        self.num_channels = num_channels  # Antal kanaler att visa i GUI
        self.running = False
        self.stream = None
        self.samplerate = samplerate
        self.device = device
        self.q = queue.Queue()
        self.gain = gain  # Volymförstärkning (1.0 = normal, 2.0 = dubbel, etc.)
        
        # Försök hitta enhetens faktiska kanalantal för att fånga alla mikrofoner
        self.device_channels = self._get_device_channels()

        margin = 10
        gap = 8
        bar_w = (self.w - margin*2 - gap*(num_channels-1)) // num_channels
        for i in range(num_channels):
            x0 = margin + i*(bar_w+gap)
            y0 = margin
            x1 = x0 + bar_w
            y1 = self.h - margin - 30  # Mer utrymme för värden
            rect = self.canvas.create_rectangle(x0, y1, x1, y0, fill="#4caf50")
            self.canvas.coords(rect, x0, y1, x1, y1)
            self.bars.append((rect, (x0, y0, x1, y1)))

        # Kanallabels
        self.labels = []
        for i in range(num_channels):
            x0,y0,x1,y1 = self.bars[i][1]
            t = self.canvas.create_text((x0+x1)//2, y1+5, text=f"CH{i+1}", anchor="n", font=("TkDefaultFont", 10))
            self.labels.append(t)
        
        # Värdelabels (dB/procent)
        self.value_labels = []
        for i in range(num_channels):
            x0,y0,x1,y1 = self.bars[i][1]
            t = self.canvas.create_text((x0+x1)//2, y1+20, text="0%", anchor="n", font=("TkDefaultFont", 9), fill="#aaa")
            self.value_labels.append(t)

    def _get_device_channels(self):
        """Hämta enhetens maximala antal ingångskanaler"""
        try:
            if self.device is None:
                # Använd standardenhet
                device_info = sd.query_devices(kind='input')
            else:
                device_info = sd.query_devices(self.device)
            
            max_channels = device_info.get('max_input_channels', self.num_channels)
            # För ReSpeaker 4-Mic Array v2.0 har ofta 6 kanaler (4 mic + 2 ref)
            # Öppna med alla tillgängliga kanaler för att fånga alla mikrofoner
            return max_channels
        except Exception as e:
            # Om det inte går att hämta info, använd num_channels som fallback
            return self.num_channels

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass
        # Normalisera int16 data (-32768 till 32767) till float (-1.0 till 1.0)
        # indata har form (frames, channels) där channels = device_channels
        normalized = indata.astype(np.float32) / 32768.0
        # Applicera gain
        normalized = normalized * self.gain
        # Beräkna RMS per kanal (axis=0 ger en RMS-värde per kanal)
        # Detta beräknar RMS för ALLA kanaler från enheten
        with np.errstate(invalid='ignore'):
            rms = np.sqrt(np.mean(np.square(normalized), axis=0))
        # Klipp till 0.0-1.0 efter gain är applicerad
        rms = np.clip(rms, 0.0, 1.0)
        self.q.put(rms)

    def start(self):
        if self.running:
            return
        self.running = True
        try:
            # Öppna stream med alla tillgängliga kanaler från enheten
            # Detta säkerställer att alla mikrofoner fångas, även om de är
            # mappade till högre kanalnummer (t.ex. kanal 4-5 på ReSpeaker)
            self.stream = sd.InputStream(
                channels=self.device_channels,
                samplerate=self.samplerate,
                dtype="int16",
                device=self.device,
                callback=self._audio_callback,
                blocksize=1024
            )
            self.stream.start()
        except Exception as e:
            self.running = False
            raise e

        self._tick()

    def stop(self):
        self.running = False
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        finally:
            self.stream = None

    def _tick(self):
        try:
            while True:
                rms = self.q.get_nowait()
                # Visa endast de första num_channels kanalerna i GUI:t
                # även om enheten har fler kanaler (t.ex. 6 kanaler men visa bara 4)
                for i in range(min(self.num_channels, len(rms))):
                    rect, (x0,y0,x1,y1) = self.bars[i]
                    height = int((y1 - y0) * (1.0 - rms[i]))
                    new_top = y0 + height
                    self.canvas.coords(rect, x0, new_top, x1, y1)
                    
                    # Uppdatera värdelabel
                    percent = int(rms[i] * 100)
                    # Beräkna dB (20 * log10(rms)), men undvik log(0)
                    if rms[i] > 0.001:
                        db = 20 * np.log10(rms[i])
                        self.canvas.itemconfig(self.value_labels[i], text=f"{percent}% ({db:.0f}dB)")
                    else:
                        self.canvas.itemconfig(self.value_labels[i], text=f"{percent}%")
        except queue.Empty:
            pass
        if self.running:
            self.canvas.after(50, self._tick)
    
    def set_gain(self, gain):
        """Uppdatera gain-värdet"""
        self.gain = max(0.1, min(10.0, gain))

# ========= GUI-app =========
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mötesinspelare")
        self.geometry("800x480")
        self.configure(bg="#111")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        # Konfigurera button-stil med vit text och vit outline
        self.style.configure("TButton", 
                           font=("Arial", 18), 
                           padding=10, 
                           foreground="white",
                           background="#333",
                           bordercolor="white",
                           lightcolor="white",
                           darkcolor="white",
                           borderwidth=2,
                           relief="solid")
        self.style.configure("Big.TButton", 
                           font=("Arial", 24), 
                           padding=16, 
                           foreground="white",
                           background="#333",
                           bordercolor="white",
                           lightcolor="white",
                           darkcolor="white",
                           borderwidth=2,
                           relief="solid")
        # Map för att behålla vit text vid interaktion
        self.style.map("TButton", 
                      foreground=[("active", "white"), ("!disabled", "white")],
                      background=[("active", "#444"), ("!disabled", "#333")])
        self.style.map("Big.TButton", 
                      foreground=[("active", "white"), ("!disabled", "white")],
                      background=[("active", "#444"), ("!disabled", "#333")])
        self.style.configure("TLabel", background="#111", foreground="white")

        # Statusrad (liten)
        self.status_var = tk.StringVar(value="Klar")
        self.time_var = tk.StringVar(value="00:00:00")

        top = tk.Frame(self, bg="#111")
        top.pack(fill="both", expand=False, pady=10)
        # Använd tk.Label istället för ttk.Label för bättre wrapping-stöd
        self.status_label = tk.Label(top, textvariable=self.status_var, font=("Arial", 14), 
                                     bg="#111", fg="white", anchor="w", justify="left", wraplength=550)
        self.status_label.pack(side="left", padx=20, fill="x", expand=True)
        ttk.Label(top, text="Tid:", font=("Arial", 20)).pack(side="right", padx=(0,5))
        ttk.Label(top, textvariable=self.time_var, font=("Arial", 20)).pack(side="right", padx=(0,20))

        # Knappar
        btns = tk.Frame(self, bg="#111")
        btns.pack(fill="x", pady=10)
        self.btn_test = ttk.Button(btns, text="Testa nivåer", style="Big.TButton", command=self.on_test_levels)
        self.btn_start = ttk.Button(btns, text="Starta inspelning", style="Big.TButton", command=self.on_start)
        self.btn_stop  = ttk.Button(btns, text="Stoppa & ladda upp", style="Big.TButton", command=self.on_stop)
        self.btn_test.pack(side="left", expand=True, fill="x", padx=10)
        self.btn_start.pack(side="left", expand=True, fill="x", padx=10)
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=10)

        # Canvas för nivåmätare
        self.canvas = tk.Canvas(self, width=760, height=300, bg="#222", highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Volymkontroll (Gain)
        gain_frame = tk.Frame(self, bg="#111")
        gain_frame.pack(fill="x", pady=5, padx=20)
        
        gain_label = ttk.Label(gain_frame, text="Volymkontroll (Gain):", font=("Arial", 14))
        gain_label.pack(side="left", padx=5)
        
        self.gain_var = tk.DoubleVar(value=1.0)
        self.gain_value_label = ttk.Label(gain_frame, text="1.0x", font=("Arial", 14), width=6)
        self.gain_value_label.pack(side="right", padx=5)
        
        self.gain_slider = ttk.Scale(
            gain_frame, 
            from_=0.1, 
            to=5.0, 
            orient="horizontal",
            variable=self.gain_var,
            command=self.on_gain_change
        )
        self.gain_slider.pack(side="left", fill="x", expand=True, padx=10)
        
        self.meter = LevelMeter(self.canvas, num_channels=CHANNELS_TEST, samplerate=SAMPLE_RATE, device=ALSA_DEVICE, gain=1.0)

        # Stor röd REC-indikator + timer i mitten
        self.rec_var = tk.StringVar(value="")
        self.rec_label = tk.Label(
            self, textvariable=self.rec_var,
            font=("Arial", 72, "bold"), fg="#ff3333", bg="#111"
        )
        self.rec_label.place(relx=0.5, rely=0.52, anchor="center")
        self.rec_label.lower()
        self._blink_on = True

        # Internt tillstånd
        self.record_proc = None
        self.record_start = None
        self.current_wav = None
        self._timer_job = None
        self.test_active = False
        self.recording_gain = 1.0  # Sparar gain-värdet som användes vid inspelning
        
        # Konfigurationshanterare
        self.config_manager = ConfigManager() if MQTT_SUPPORT else None
        
        # MQTT-klient
        self.mqtt_client = None
        if MQTT_SUPPORT:
            try:
                mqtt_config = get_mqtt_config_from_env()
                if mqtt_config.get("enabled"):
                    self.mqtt_client = MQTTClient(mqtt_config)
                    self.mqtt_client.set_callbacks(
                        on_start=self.mqtt_on_start,
                        on_stop=self.mqtt_on_stop,
                        on_test=self.mqtt_on_test,
                        on_config_update=self.mqtt_on_config_update
                    )
                    self.mqtt_client.connect()
                    # Publicera initial konfiguration
                    self.mqtt_client.publish_config(self.config_manager.get_all())
                    logging.info("MQTT-klient initialiserad och ansluten")
            except Exception as e:
                logging.error(f"Kunde inte initiera MQTT-klient: {e}")
                self.mqtt_client = None

    # ---------- Handlers ----------
    def on_gain_change(self, value):
        """Hantera ändring av gain-slider"""
        gain = float(value)
        self.gain_value_label.configure(text=f"{gain:.1f}x")
        self.meter.set_gain(gain)
    
    # ---------- MQTT Callbacks ----------
    def mqtt_on_start(self):
        """Hantera start-kommando från MQTT"""
        # Schemalägg kommando i main thread (Tkinter är inte trådsäker)
        self.after(0, self.on_start)
    
    def mqtt_on_stop(self):
        """Hantera stopp-kommando från MQTT"""
        self.after(0, self.on_stop)
    
    def mqtt_on_test(self):
        """Hantera test-kommando från MQTT"""
        self.after(0, self.on_test_levels)
    
    def mqtt_on_config_update(self, config_updates):
        """Hantera konfigurationsuppdatering från MQTT"""
        if not self.config_manager:
            return
        
        # Uppdatera konfiguration
        self.config_manager.update(config_updates)
        
        # Hantera speciella konfigurationer
        if "wifi_ssid" in config_updates and "wifi_password" in config_updates:
            self.config_manager.set_wifi_credentials(
                config_updates["wifi_ssid"],
                config_updates["wifi_password"]
            )
        
        # Publicera uppdaterad konfiguration
        if self.mqtt_client:
            self.mqtt_client.publish_config(self.config_manager.get_all())
        
        logging.info(f"Konfiguration uppdaterad via MQTT: {list(config_updates.keys())}")
    
    def on_test_levels(self):
        if self.record_proc is not None:
            self.flash_status("Kan inte testa nivåer under inspelning", warn=True)
            return
        try:
            if not self.test_active:
                self.meter.start()
                self.test_active = True
                # Visa information om hur många kanaler som fångas vs visas
                if self.meter.device_channels != self.meter.num_channels:
                    self.status_var.set(f"Testläge: {self.meter.device_channels} ch fångade, {self.meter.num_channels} visas")
                else:
                    self.status_var.set(f"Testläge: visa nivåer ({self.meter.num_channels} ch)")
                self.btn_test.configure(text="Stoppa test")
            else:
                self.meter.stop()
                self.test_active = False
                self.status_var.set("Klar")
                self.btn_test.configure(text="Testa nivåer")
        except Exception as e:
            self.flash_status(f"Testfel: {e}", warn=True)

    def on_start(self):
        if self.record_proc is not None:
            return
        if self.test_active:
            self.meter.stop()
            self.test_active = False
            self.btn_test.configure(text="Testa nivåer")

        fname = f"meeting-{ts_name()}.wav"
        self.current_wav = AUDIO_DIR / fname
        
        # Spara gain-värdet som ska användas vid konvertering
        self.recording_gain = self.gain_var.get()

        cmd = ["arecord", "-f", FORMAT, "-r", str(SAMPLE_RATE), "-c", "1", str(self.current_wav)]
        if ALSA_DEVICE:
            cmd = ["arecord", "-D", ALSA_DEVICE, "-f", FORMAT, "-r", str(SAMPLE_RATE), "-c", "1", str(self.current_wav)]

        try:
            self.record_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            self.record_start = time.time()
            self.status_var.set(f"Inspelning pågår → {self.current_wav.name}")
            self.rec_label.lift()
            self._blink_on = True
            self.tick_timer()
            # Publicera status till MQTT
            if self.mqtt_client:
                room = self.config_manager.get("room", "") if self.config_manager else ""
                self.mqtt_client.publish_status("recording", {"filename": self.current_wav.name, "room": room})
        except Exception as e:
            self.record_proc = None
            self.flash_status(f"Kunde inte starta inspelning: {e}", warn=True)

    def on_stop(self):
        if self.record_proc is None:
            return
        self.status_var.set("Stoppar inspelning…")
        self.stop_recording()
        self.rec_var.set("")
        self.rec_label.lower()
        # Publicera status till MQTT
        if self.mqtt_client:
            self.mqtt_client.publish_status("processing")
        threading.Thread(target=self._convert_and_upload, daemon=True).start()

    def stop_recording(self):
        try:
            self.record_proc.terminate()
            try:
                self.record_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.record_proc.kill()
        finally:
            self.record_proc = None
            self.record_start = None
            if self._timer_job:
                self.after_cancel(self._timer_job)
                self._timer_job = None

    def _convert_and_upload(self):
        wav = self.current_wav
        gain = self.recording_gain  # Hämta gain-värdet som sparades vid inspelningsstart
        self.current_wav = None
        if not wav or not wav.exists():
            self.flash_status("Fil saknas efter stopp", warn=True)
            if self.mqtt_client:
                self.mqtt_client.publish_status("error", {"message": "Fil saknas efter stopp"})
            return

        self.status_var.set("Komprimerar och förbättrar ljud (WAV→FLAC)…")
        if self.mqtt_client:
            self.mqtt_client.publish_status("converting")
        
        ok, flac_path, msg = wav_to_flac(wav, gain=gain)
        if not ok:
            self.flash_status(msg, warn=True)
            if self.mqtt_client:
                self.mqtt_client.publish_status("error", {"message": msg})
            return

        self.status_var.set("Laddar upp…")
        if self.mqtt_client:
            self.mqtt_client.publish_status("uploading")
        
        ok, info = upload_file(flac_path)
        if ok:
            self.flash_status(f"Klar! Uppladdad: {info}")
            if self.mqtt_client:
                self.mqtt_client.publish_status("ready")
                self.mqtt_client.publish_recording_complete(flac_path.name, info)
        else:
            self.flash_status(f"Uppladdning misslyckades: {info}", warn=True)
            if self.mqtt_client:
                self.mqtt_client.publish_status("error", {"message": f"Uppladdning misslyckades: {info}"})

    def tick_timer(self):
        if self.record_proc is not None and self.record_start is not None:
            elapsed = time.time() - self.record_start
            if elapsed > MAX_HOURS * 3600:
                self.on_stop()
                return

            self.time_var.set(human_duration(elapsed))
            symbol = "●" if self._blink_on else "○"
            self._blink_on = not self._blink_on
            self.rec_var.set(f"{symbol}  REC  {human_duration(elapsed)}")
            self._timer_job = self.after(500, self.tick_timer)
        else:
            self.time_var.set("00:00:00")
            self.rec_var.set("")

    def flash_status(self, text, warn=False):
        self.status_var.set(text)
        if warn:
            self.configure(bg="#330000")
            self.after(600, lambda: self.configure(bg="#111"))
        else:
            self.configure(bg="#112211")
            self.after(400, lambda: self.configure(bg="#111"))
    
    def cleanup(self):
        """Städa upp resurser vid avslut"""
        if self.mqtt_client:
            try:
                self.mqtt_client.disconnect()
                logging.info("MQTT-klient frånkopplad")
            except Exception as e:
                logging.error(f"Fel vid frånkoppling av MQTT: {e}")

def main():
    try:
        app = App()
        # Registrera cleanup vid avslut
        app.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup(), app.destroy()))
    except tk.TclError as exc:
        print("Kunde inte starta GUI:", exc, file=sys.stderr)
        if not os.environ.get("DISPLAY"):
            print("Miljövariabeln DISPLAY saknas. Kör i en miljö med grafikstöd eller sätt DISPLAY.", file=sys.stderr)
        sys.exit(1)
    app.mainloop()

if __name__ == "__main__":
    main()
