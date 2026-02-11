# Twitch Viral Clip Automator 🚀

Ein KI-gestütztes Tool zur automatischen Erstellung von viralen Twitch-Clips (9:16 Format) aus VODs.

## Features
- **Unbegrenzte Länge**: Unterstützt 4-6 Stunden Streams durch optimierte Prompting-Strategie.
- **Download**: Lädt Twitch-VODs in höchster Qualität herunter (yt-dlp).
- **Transkription**: Lokale KI-Transkription mit Wort-Timestamps (Faster-Whisper).
- **KI-Analyse**: Identifiziert virale Momente, bewertet diese und erkennt automatisch die Facecam-Position (Google Gemini 1.5 Pro).
- **Smart Editing**: Erstellt automatisch 9:16 Clips mit Facecam oben und Gameplay unten (MoviePy).
- **Modern UI**: Dunkles "Space Theme" Design mit Electron.

## Installation & Setup

### Voraussetzungen
1. **Python 3.10+**
2. **Node.js 18+**
3. **FFmpeg** (muss im System-Pfad sein)
4. **Google Gemini API Key**: Erhältlich unter [ai.google.dev](https://ai.google.dev/).

### Lokale Entwicklung
1. Repository klonen.
2. Python-Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
3. Node-Abhängigkeiten installieren:
   ```bash
   npm install
   ```
4. `.env` Datei erstellen (basierend auf `.env.example`) und API-Key eintragen:
   ```env
   GEMINI_API_KEY=dein_api_key
   ```
5. App starten:
   ```bash
   npm start
   ```

## Workflow
1. Füge einen Twitch-VOD Link in das Programm ein.
2. Das Programm lädt das VOD herunter und transkribiert es lokal.
3. Gemini analysiert den Text auf Highlights und findet die Facecam im Video.
4. Wähle die besten Clips aus der Liste aus und klicke auf "Exportieren".
5. Der fertige Clip wird im 9:16 Format im Ordner `clips/` gespeichert.

## Build (Windows)
Der Build erfolgt automatisch via GitHub Actions bei einem Push auf den `main` Branch. Die `.exe` wird als GitHub Release bereitgestellt.

## API-Limits & Hardware
- **Gemini 1.5 Pro**: Das Modell hat ein sehr großes Kontext-Fenster, was die Analyse kompletter Streams ermöglicht. Achten Sie auf Ihre API-Quota im Google AI Studio.
- **Hardware**: Die lokale Transkription profitiert massiv von einer NVIDIA GPU (CUDA). Das Programm ist aktuell auf CPU-Nutzung vorkonfiguriert, kann aber in `backend/app.py` auf `device="cuda"` umgestellt werden.

## Lizenz
MIT
