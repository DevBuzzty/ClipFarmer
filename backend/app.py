import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from downloader import Downloader
from transcriber import Transcriber
from analyzer import Analyzer
from editor import Editor
from audio_analyzer import AudioAnalyzer
from social_uploader import SocialUploader
from utils import extract_screenshot, refine_facecam_crop
from task_manager import TaskManager
import json
import threading
import uuid
import time
import requests
from flask import redirect

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize modules
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY', ''),
        "WHISPER_MODEL": "base",
        "USE_GPU": False,
        "LAYOUT": "stack",
        "CAPTIONS": True
    }

config = load_config()

# Global module instances (lazy loaded)
_downloader = None
_transcriber = None
_analyzer = None
_editor = None
_uploader = None

def get_downloader():
    global _downloader
    if _downloader is None:
        _downloader = Downloader()
    return _downloader

def get_transcriber():
    global _transcriber
    if _transcriber is None:
        device = "cuda" if config.get('USE_GPU') else "cpu"
        model_size = config.get('WHISPER_MODEL', 'base')
        try:
            _transcriber = Transcriber(model_size=model_size, device=device)
        except Exception as e:
            print(f"Error initializing Transcriber (Whisper): {e}")
            # Fallback to CPU if CUDA fails
            if device == "cuda":
                _transcriber = Transcriber(model_size=model_size, device="cpu")
            else:
                raise e
    return _transcriber

def get_analyzer():
    global _analyzer
    if _analyzer is None:
        api_key = config.get('GEMINI_API_KEY')
        if not api_key:
            raise Exception("Gemini API Key fehlt in den Einstellungen!")
        _analyzer = Analyzer(api_key=api_key)
    return _analyzer

def get_editor():
    global _editor
    if _editor is None:
        _editor = Editor(
            layout=config.get('LAYOUT', 'stack'),
            show_captions=config.get('CAPTIONS', True)
        )
    return _editor

def get_uploader():
    global _uploader
    if _uploader is None:
        _uploader = SocialUploader(config)
    return _uploader

# Global state
current_video = {
    "path": None,
    "facecam_coords": None,
    "gameplay_coords": None,
    "transcript_words": None
}

task_manager = TaskManager()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)

@app.route('/twitch/login', methods=['GET'])
def twitch_login():
    client_id = config.get('TWITCH_CLIENT_ID')
    redirect_uri = f"http://localhost:{os.getenv('PORT', 5001)}/twitch/callback"
    scope = "clips:edit"
    url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    return jsonify({"url": url})

@app.route('/twitch/create_clip', methods=['POST'])
def create_twitch_clip():
    data = request.json
    video_id = data.get('video_id')
    # video_id from twitch is needed.
    # Note: Create Clip API usually works on a broadcaster ID (channel) and returns a clip of what is currently live,
    # OR you can use it on a VOD? Wait.
    # Actually, the Helix "Create Clip" API is for LIVE streams.
    # For VODs, there is no direct "Create Clip from VOD" API in Helix that I'm aware of,
    # except maybe through the browser/embed.
    # HOWEVER, you can use the 'Create Clip' on a broadcaster ID.

    # If the user wants to clip from a VOD, the best way IS the URL we already have.
    # But let's see if we can at least automate the 'Create Clip' if they are live.
    # Since the user requested "direkt einen clip von besagter stelle auf twitch erstellt",
    # and they are processing VODs, the Link is the most reliable way.

    # Let's check if there is a way to create a clip from a VOD via API.
    # Helix documentation says "Creates a clip from the broadcaster’s stream." - it usually means live.

    return jsonify({"error": "Twitch Helix API erlaubt Clipping nur von Live-Streams. Für VODs bitte den Link nutzen."}), 400

@app.route('/twitch/callback', methods=['GET'])
def twitch_callback():
    code = request.args.get('code')
    client_id = config.get('TWITCH_CLIENT_ID')
    client_secret = config.get('TWITCH_CLIENT_SECRET')
    redirect_uri = f"http://localhost:{os.getenv('PORT', 5001)}/twitch/callback"

    token_url = "https://id.twitch.tv/oauth2/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    try:
        response = requests.post(token_url, data=payload, timeout=10)
        res_data = response.json()
    except Exception as e:
        return f"<h1>Fehler beim Login</h1><p>Timeout oder Verbindungsfehler zur Twitch API: {str(e)}</p>"

    if "access_token" in res_data:
        config["TWITCH_ACCESS_TOKEN"] = res_data["access_token"]
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return "<h1>Twitch Login Erfolgreich!</h1><p>Du kannst dieses Fenster jetzt schließen.</p>"
    else:
        return f"<h1>Fehler beim Login</h1><p>{res_data.get('message', 'Unbekannter Fehler')}</p>"

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    global config, _transcriber, _analyzer, _uploader, _editor
    if request.method == 'GET':
        return jsonify(load_config())
    else:
        new_config = request.json
        with open(CONFIG_FILE, 'w') as f:
            json.dump(new_config, f)
        config = new_config
        # Reset modules so they re-initialize with new settings
        _transcriber = None
        _analyzer = None
        _uploader = None
        _editor = None
        return jsonify({"success": True})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id, "starting")

    def run_analyze():
        try:
            task_manager.update_task(task_id, "downloading", progress=10)
            video_path = get_downloader().download_video(url)
            current_video["path"] = video_path

            task_manager.update_task(task_id, "transcribing", progress=30)
            audio_path = get_downloader().extract_audio(video_path)
            transcript_data = get_transcriber().transcribe(audio_path)
            current_video["transcript_words"] = transcript_data.get("words")

            task_manager.update_task(task_id, "audio_analysis", progress=60)
            audio_analyzer = AudioAnalyzer(audio_path)
            hype_segments = audio_analyzer.get_hype_segments()

            task_manager.update_task(task_id, "analyzing", progress=80)
            # Pass hype segments to analyzer for better results
            clips = get_analyzer().find_viral_clips(transcript_data, hype_segments=hype_segments)

            task_manager.update_task(task_id, "detecting_facecam", progress=90)
            sample_times = [300, 600, 1200]
            for t in sample_times:
                screenshot_path = f"screenshot_{t}.jpg"
                if extract_screenshot(video_path, t, screenshot_path):
                    coords = get_analyzer().detect_facecam(screenshot_path)
                    if coords and coords.get('facecam'):
                        refined_face = refine_facecam_crop(screenshot_path, coords.get('facecam'))
                        current_video["facecam_coords"] = refined_face
                        current_video["gameplay_coords"] = coords.get('gameplay')
                        break

            task_manager.update_task(task_id, "completed", progress=100, result={"clips": clips})
            # Cleanup audio and screenshots
            if os.path.exists(audio_path):
                os.remove(audio_path)
            for t in sample_times:
                s_path = f"screenshot_{t}.jpg"
                if os.path.exists(s_path):
                    os.remove(s_path)
        except Exception as e:
            task_manager.update_task(task_id, "failed", error=str(e))

    threading.Thread(target=run_analyze).start()
    return jsonify({"task_id": task_id})

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    platform = data.get('platform')
    video_path = data.get('video_path')
    title = data.get('title', 'Twitch Clip')
    description = data.get('description', '')
    tags = data.get('tags', [])

    if not video_path or not os.path.exists(video_path):
        return jsonify({"error": "Video Datei nicht gefunden"}), 400

    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id, f"uploading_to_{platform}")

    def run_upload():
        try:
            if platform == 'youtube':
                video_id = get_uploader().upload_to_youtube(video_path, title, description, tags)
                task_manager.update_task(task_id, "completed", progress=100, result={"video_id": video_id})
            elif platform == 'tiktok':
                res = get_uploader().upload_to_tiktok(video_path, description)
                task_manager.update_task(task_id, "completed", progress=100, result={"res": res})
            else:
                task_manager.update_task(task_id, "failed", error="Unbekannte Plattform")
        except Exception as e:
            task_manager.update_task(task_id, "failed", error=str(e))

    threading.Thread(target=run_upload).start()
    return jsonify({"task_id": task_id})

@app.route('/export', methods=['POST'])
def export():
    data = request.json
    clip_data = data.get('clip')
    if not clip_data or not current_video["path"]:
        return jsonify({"error": "Missing data or video not analyzed"}), 400

    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id, "exporting")

    def run_export():
        try:
            output_filename = f"clip_{int(clip_data['start'])}.mp4"
            facecam = current_video["facecam_coords"] or [0, 0, 300, 300]
            gameplay = current_video["gameplay_coords"] or [0, 0, 1000, 1000]

            output_path = get_editor().process_clip(
                current_video["path"],
                clip_data['start'],
                clip_data['end'],
                facecam,
                gameplay,
                output_filename,
                use_gpu=config.get('USE_GPU', False),
                transcript_words=current_video.get("transcript_words")
            )
            task_manager.update_task(task_id, "completed", progress=100, result={"path": output_path})
        except Exception as e:
            task_manager.update_task(task_id, "failed", error=str(e))

    threading.Thread(target=run_export).start()
    return jsonify({"task_id": task_id})

if __name__ == '__main__':
    # Use 127.0.0.1 for better reliability on Windows
    port = int(os.getenv('PORT', 5001))
    app.run(host='127.0.0.1', port=port)
