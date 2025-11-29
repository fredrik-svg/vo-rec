# ElevenLabs Speech-to-Text - Ljudformat och kvalitet

## Sammanfattning

När du använder ElevenLabs Speech-to-Text (Scribe-modellen) är du **inte begränsad till mono-ljud**. Tjänsten stöder både mono och stereo/flerkanaligt ljud med upp till 5 kanaler.

## Ljudformat som stöds

ElevenLabs Speech-to-Text accepterar följande ljudformat:

| Format | Beskrivning |
|--------|-------------|
| MP3 | Komprimerat format, bra balans mellan storlek och kvalitet |
| WAV | Okomprimerat PCM-ljud, högsta kvalitet |
| FLAC | Förlustfritt komprimerat, bästa kompromiss för arkivering |
| OGG | Öppet komprimerat format |
| AAC | Avancerat komprimerat format |
| OPUS | Modernt komprimerat format, optimerat för tal |
| WEBM | Webbaserat containerformat |
| MP4 | Video/ljud-container (ljudspår extraheras) |

## Mono vs Stereo

### Mono (1 kanal)
- **Fullt stödd** för transkribering
- Stöd för **speaker diarization** (upp till 32 talare)
- Lämpligt för de flesta inspelningsscenarion
- **Rekommenderat för enklare användning**

### Stereo/Flerkanal (2-5 kanaler)
- **Fullt stödd** via multichannel-läge
- Upp till **5 kanaler** stöds
- Idealiskt när varje talare har en egen kanal (t.ex. intervjuer, poddar)
- Kräver att API-parametern `use_multi_channel: true` sätts
- Ger automatisk talaridentifiering baserat på kanaltillhörighet

### När ska man använda stereo/flerkanal?
- **Intervjuer**: Intervjuare på vänster kanal, intervjuobjekt på höger
- **Poddar**: Varje deltagare på en egen kanal
- **Konferenssamtal**: Separata kanaler för olika deltagare
- **Studioinspelningar**: Flera mikrofoner kopplade till egna kanaler

## Samplingsfrekvens och bitrate

### Stödda samplingsfrekvenser
| Frekvens | Användning |
|----------|------------|
| 8 kHz | Telefoni, lägsta kvalitet |
| 16 kHz | Standardkvalitet för tal (rekommenderat minimum) |
| 22.05 kHz | Bra talkvalitet |
| 24 kHz | Hög talkvalitet |
| 44.1 kHz | CD-kvalitet |
| 48 kHz | Studiekvalitet |

### Bitrater för MP3
- 32 kbps - 192 kbps beroende på prenumerationstyp

### PCM och Opus
- PCM: 8 kHz till 48 kHz
- Opus: Normalt 48 kHz

## Filstorleks- och längdbegränsningar

| Begränsning | Värde |
|-------------|-------|
| Maximal filstorlek | 1 GB (upp till 3 GB via webgränssnittet) |
| Maximal längd | 4,5 timmar per fil |

## Rekommendationer för vo-rec

### Nuvarande konfiguration
Vo-rec spelar in i:
- **Format**: WAV (16-bit PCM) → FLAC
- **Samplingsfrekvens**: 16 kHz
- **Kanaler**: Mono (1 kanal)

### Alternativ för högre kvalitet

Om du vill spela in med högre kvalitet för ElevenLabs-transkribering kan du justera följande i `src/meetrec_gui.py`:

```python
# Nuvarande (optimerat för tal-transkribering)
SAMPLE_RATE = 16000  # 16 kHz
# Inspelning sker i mono med arecord

# Alternativ för högre kvalitet
SAMPLE_RATE = 48000  # 48 kHz för studiekvalitet
# Ändra "-c", "1" till "-c", "2" för stereo i arecord-kommandot
```

### Stereo-inspelning (valfritt)

För att aktivera stereo-inspelning, ändra inspelningskommandot i `on_start()`:

```python
# Från:
cmd = ["arecord", "-f", FORMAT, "-r", str(SAMPLE_RATE), "-c", "1", str(self.current_wav)]

# Till:
cmd = ["arecord", "-f", FORMAT, "-r", str(SAMPLE_RATE), "-c", "2", str(self.current_wav)]
```

**Notera**: Stereo-inspelning kräver att din mikrofon/ljudkort stöder stereo-inspelning.

## Best practices

1. **För enkel transkribering**: Mono 16 kHz räcker utmärkt för de flesta tal-till-text-användningsfall

2. **För speaker diarization**: Mono fungerar bra med ElevenLabs automatiska talaridentifiering (upp till 32 talare)

3. **För separata talare**: Använd stereo/flerkanal om varje talare har en dedikerad mikrofon/kanal

4. **För arkivering**: FLAC ger förlustfri komprimering och stöds av ElevenLabs

5. **Undvik onödigt hög kvalitet**: 48 kHz ger ingen förbättring för tal-transkribering jämfört med 16 kHz, men ökar filstorleken markant

## Referenser

- [ElevenLabs Audio Format Support](https://help.elevenlabs.io/hc/en-us/articles/15754340124305-What-audio-formats-do-you-support)
- [ElevenLabs Speech to Text Documentation](https://elevenlabs.io/docs/capabilities/speech-to-text)
- [ElevenLabs Multichannel Transcription](https://elevenlabs.io/docs/cookbooks/speech-to-text/multichannel-transcription)
