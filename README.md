# ViraFlow v2.0 🚀
### AI-Powered Twitch Viral Clip Automator (Deep Dark Space Edition)

ViraFlow ist ein Premium-Tool zur automatisierten Erstellung von Social-Media-Clips (9:16) aus Twitch-VODs.

## Features
- **Deep Space UI**: Ein modernes, dunkles Design (Jules-Style).
- **Intelligente Analyse**: Kombiniert Whisper-Transkription mit Audio-Hype-Erkennung (RMS) und Gemini 1.5 Pro.
- **Auto-Layout**: Erkennt automatisch Facecam und Gameplay; unterstützt Stacked und Overlay Layouts.
- **Animated Captions**: Automatische, animierte Untertitel für maximale Viralität.
- **GPU Acceleration**: Unterstützt NVENC für blitzschnelles Rendering.

## Installation & Setup

### Voraussetzungen
1. **Python 3.10+** & **Node.js 20+**
2. **FFmpeg** (muss im System-Pfad erreichbar sein)
3. **Google Gemini API Key**

### Lokale Entwicklung
1. Klone das Repository.
2. Installiere Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   npm install
   ```
3. Starte die App:
   ```bash
   npm start
   ```

## Build (Windows)
Um eine installierbare `.exe` zu erstellen:
```bash
npm run dist
```
Die fertige Datei befindet sich anschließend im Ordner `dist/`.

## Lizenz
MIT
