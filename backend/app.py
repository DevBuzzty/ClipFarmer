import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from downloader import Downloader
from transcriber import Transcriber
from analyzer import Analyzer
from editor import Editor
from social_uploader import SocialUploader
from utils import extract_screenshot
import json

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
        "USE_GPU": False
    }

config = load_config()

downloader = Downloader()
uploader = SocialUploader(config)
transcriber = Transcriber(model_size=config.get('WHISPER_MODEL', 'base'), device="cuda" if config.get('USE_GPU') else "cpu")
analyzer = Analyzer(api_key=config.get('GEMINI_API_KEY'))
editor = Editor()

# Global state to keep track of current video info
current_video = {
    "path": None,
    "facecam_coords": None,
    "gameplay_coords": None
}

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    global config, transcriber, analyzer, uploader
    if request.method == 'GET':
        return jsonify(load_config())
    else:
        new_config = request.json
        with open(CONFIG_FILE, 'w') as f:
            json.dump(new_config, f)
        config = new_config
        # Re-initialize modules with new settings
        transcriber = Transcriber(model_size=config.get('WHISPER_MODEL', 'base'), device="cuda" if config.get('USE_GPU') else "cpu")
        analyzer = Analyzer(api_key=config.get('GEMINI_API_KEY'))
        uploader = SocialUploader(config)
        return jsonify({"success": True})

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # 1. Download Video
        video_path = downloader.download_video(url)
        current_video["path"] = video_path

        # 2. Extract Audio & Transcribe
        audio_path = downloader.extract_audio(video_path)
        transcript = transcriber.transcribe(audio_path)

        # 3. Find Viral Clips
        clips = analyzer.find_viral_clips(transcript)

        # 4. Detect Facecam (sample multiple points to avoid starting screens)
        sample_times = [300, 600, 1200] # 5, 10, 20 minutes
        for t in sample_times:
            screenshot_path = f"screenshot_{t}.jpg"
            if extract_screenshot(video_path, t, screenshot_path):
                coords = analyzer.detect_facecam(screenshot_path)
                if coords and coords.get('facecam'):
                    current_video["facecam_coords"] = coords.get('facecam')
                    current_video["gameplay_coords"] = coords.get('gameplay')
                    break

        return jsonify({"clips": clips})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

    try:
        if platform == 'youtube':
            video_id = uploader.upload_to_youtube(video_path, title, description, tags)
            return jsonify({"success": True, "video_id": video_id})
        elif platform == 'tiktok':
            # Placeholder call
            res = uploader.upload_to_tiktok(video_path, description)
            return jsonify({"success": True, "res": res})
        else:
            return jsonify({"error": "Unbekannte Plattform"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/export', methods=['POST'])
def export():
    data = request.json
    clip_data = data.get('clip')
    if not clip_data or not current_video["path"]:
        return jsonify({"error": "Missing data or video not analyzed"}), 400

    try:
        output_filename = f"clip_{int(clip_data['start'])}.mp4"

        # Use detected coords or defaults
        facecam = current_video["facecam_coords"] or [0, 0, 300, 300] # dummy fallback
        gameplay = current_video["gameplay_coords"] or [0, 0, 1000, 1000] # dummy fallback

        output_path = editor.process_clip(
            current_video["path"],
            clip_data['start'],
            clip_data['end'],
            facecam,
            gameplay,
            output_filename,
            use_gpu=config.get('USE_GPU', False)
        )

        return jsonify({"success": True, "path": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
