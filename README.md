# ViraFlow v2.0 - AI Twitch Automator

ViraFlow ist ein professionelles Tool zur Automatisierung von Twitch-Highlights. Es nutzt KI, um virale Momente in VODs zu finden, sie automatisch in ein vertikales 9:16 Format zu schneiden (inkl. Facecam-Fokus) und für Social Media (TikTok, YouTube Shorts, Reels) zu exportieren.

## Features
- **KI-Analyse:** Nutzt Google Gemini 1.5 Pro für semantisches Verständnis und Highlights.
- **Transkription:** Lokale, schnelle Transkription mit `faster-whisper`.
- **Intelligenter Schnitt:** Automatische Erkennung von Facecam und Gameplay; Stacking auf 9:16.
- **Premium UI:** Modernes "Deep Dark Space" Design mit Flet (Python).
- **Automatisierte Captions:** Animierte, farbige Untertitel im viralen Stil.
- **Hardware-Beschleunigung:** Unterstützung für NVIDIA GPU (NVENC).

## Installation

### Voraussetzungen
- Python 3.10+
- FFmpeg (muss im PATH sein)

### Setup
1. Repository klonen:
   ```bash
   git clone <repo-url>
   cd twitch-viral-clip-automator
   ```
2. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. App starten:
   ```bash
   python main.py
   ```

## Build (EXE erstellen)
Um eine Windows-Executable zu erstellen:
```bash
python -m PyInstaller flet_build.spec
```
Das Ergebnis befindet sich im Ordner `dist/ViraFlow`.

## Konfiguration
Trage deinen **Gemini API Key** in den Einstellungen der App ein. Du kannst dort auch das Whisper-Modell und das Video-Layout anpassen.

## Credits & Architektur
ViraFlow v2.0 nutzt eine moderne, einheitliche Python-Architektur basierend auf **Flet**. Dies umgeht IPC-Probleme und sorgt für maximale Stabilität bei der Videoverarbeitung.
