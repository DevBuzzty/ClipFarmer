# Twitch Viral Clip Automator 🚀

Ein KI-gestütztes Tool zur automatischen Erstellung von viralen Twitch-Clips (9:16 Format) aus VODs.

## Features
- **Unbegrenzte Länge**: Unterstützt 4-6 Stunden Streams durch optimierte Prompting-Strategie.
- **Social Media Upload**: Direkter Upload zu **YouTube Shorts** und Vorbereitung für **TikTok**.
- **Twitch Integration**: Direkte Links zum manuellen Clipping auf Twitch.
- **KI-Analyse (Enhanced)**: Gemini 1.5 Pro generiert automatisch SEO-Titel, Beschreibungen und Hashtags.
- **Settings Tab**: Zentrale Verwaltung von API-Keys, Social Logins und Performance (GPU NVENC).
- **Batch Export**: Alle identifizierten Clips mit einem Klick exportieren.
- **Download**: Lädt Twitch-VODs in höchster Qualität herunter (yt-dlp).
- **Transkription**: Lokale KI-Transkription mit Wort-Timestamps (Faster-Whisper).
- **Smart Editing**: Erstellt automatisch 9:16 Clips mit Facecam oben und Gameplay unten (MoviePy).
- **Modern UI**: Dunkles "Space Theme" Design mit Electron.

## Installation & Setup

### Voraussetzungen
1. **Python 3.10+**
2. **Node.js 18+**
3. **FFmpeg** (muss im System-Pfad sein)
4. **Google Gemini API Key**: Erhältlich unter [ai.google.dev](https://ai.google.dev/).

## Twitch API Setup (OAuth)
Um Clips effizient zu erstellen oder die API zu nutzen:
1. Gehen Sie auf die [Twitch Developer Console](https://dev.twitch.tv/console).
2. Erstellen Sie eine neue App (Anwendung).
3. Setzen Sie die **OAuth Redirect URL** auf: `http://localhost:5000/twitch/callback`
4. Kopieren Sie die **Client ID** und das **Client Secret** in die Einstellungen der App.

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

Es gibt zwei Wege, die `.exe` zu erstellen:

### 1. Automatisch über GitHub (Empfohlen)
Da das Projekt für GitHub Actions konfiguriert ist, wird bei jedem **Push auf den `main` Branch** automatisch ein Build gestartet.
- Gehen Sie in Ihrem GitHub-Repository auf den Tab **"Actions"**.
- Sobald der Workflow "Build and Release Windows App" abgeschlossen ist, finden Sie die fertige `.exe` unter **"Releases"** auf der rechten Seite der Repository-Startseite.

### 2. Lokal auf Ihrem PC
Wenn Sie die `.exe` manuell auf Ihrem Windows-Rechner erstellen möchten:

1. **Backend kompilieren**:
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --distpath frontend/backend_dist --collect-all faster_whisper --collect-all moviepy backend/app.py
   ```
   Dies erstellt eine `app.exe` im Ordner `frontend/backend_dist`.

2. **Frontend & App verpacken**:
   ```bash
   npm run build
   ```
   Die fertige App (als Portable `.exe` oder Installer) befindet sich danach im Ordner `dist/`.

> **Hinweis**: Für den lokalen Build müssen alle Abhängigkeiten aus `requirements.txt` und `package.json` installiert sein.

## API-Limits & Hardware
- **Gemini 1.5 Pro**: Das Modell hat ein sehr großes Kontext-Fenster, was die Analyse kompletter Streams ermöglicht. Achten Sie auf Ihre API-Quota im Google AI Studio.
- **Hardware**: Die lokale Transkription profitiert massiv von einer NVIDIA GPU (CUDA). Das Programm ist aktuell auf CPU-Nutzung vorkonfiguriert, kann aber in `backend/app.py` auf `device="cuda"` umgestellt werden.

## Lizenz
MIT
