import os
import json
import uuid
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from downloader import Downloader
from transcriber import Transcriber
from analyzer import Analyzer
from editor import Editor
from audio_analyzer import AudioAnalyzer
from uploader import SocialUploader
from task_manager import TaskManager
from utils import extract_screenshot, refine_facecam_crop

load_dotenv()

app = Flask(__name__)
CORS(app)

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except: pass
    return {
        "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY', ''),
        "WHISPER_MODEL": "base",
        "USE_GPU": False,
        "LAYOUT": "stack",
        "CAPTIONS": True
    }

config = load_config()
task_manager = TaskManager()

# Module instances (lazy loaded or updated on config change)
_modules = {}

def get_module(name):
    if name not in _modules:
        if name == 'downloader': _modules[name] = Downloader()
        elif name == 'transcriber':
            _modules[name] = Transcriber(model_size=config.get('WHISPER_MODEL', 'base'),
                                       device="cuda" if config.get('USE_GPU') else "cpu")
        elif name == 'analyzer':
            _modules[name] = Analyzer(api_key=config.get('GEMINI_API_KEY'))
        elif name == 'editor':
            _modules[name] = Editor(layout=config.get('LAYOUT', 'stack'),
                                   show_captions=config.get('CAPTIONS', True))
        elif name == 'uploader': _modules[name] = SocialUploader(config)
    return _modules.get(name)

current_video_data = {"path": None, "words": None, "facecam": None, "gameplay": None}

@app.route('/health')
def health(): return jsonify({"status": "healthy"})

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global config, _modules
    if request.method == 'GET':
        return jsonify(config)
    else:
        config.update(request.json)
        with open(CONFIG_FILE, 'w') as f: json.dump(config, f)
        _modules = {} # Clear cache
        return jsonify({"success": True})

@app.route('/status/<task_id>')
def status(task_id):
    t = task_manager.get_task(task_id)
    return jsonify(t) if t else (jsonify({"error": "Not found"}), 404)

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.json.get('url')
    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id, "downloading", 10)

    def run():
        try:
            # 1. Download
            path = get_module('downloader').download_video(url)
            current_video_data["path"] = path

            # 2. Transcribe
            task_manager.update_task(task_id, "transcribing", 30)
            audio = get_module('downloader').extract_audio(path)
            res = get_module('transcriber').transcribe(audio)
            current_video_data["words"] = res["words"]

            # 3. Audio Analysis
            task_manager.update_task(task_id, "audio_analysis", 50)
            aa = AudioAnalyzer(audio)
            hype = aa.get_hype_segments()

            # 4. AI Viral Search
            task_manager.update_task(task_id, "ai_search", 70)
            clips = get_module('analyzer').find_viral_clips(res, hype)

            # Add Twitch timestamp URLs
            for clip in clips:
                start_sec = int(clip['start'])
                h = start_sec // 3600
                m = (start_sec % 3600) // 60
                s = start_sec % 60
                clip['twitch_url'] = f"{url}?t={h}h{m}m{s}s"

            # 5. Facecam Detection with Multi-Frame Sampling
            task_manager.update_task(task_id, "detecting_layout", 90)
            best_facecam = None
            best_gameplay = None

            # Try 3 different timestamps to find the best layout (300s, 600s, 900s)
            for ts in [300, 600, 900]:
                shot = f"temp_shot_{ts}.jpg"
                if extract_screenshot(path, ts, shot):
                    coords = get_module('analyzer').detect_facecam(shot)
                    if coords:
                        refined = refine_facecam_crop(shot, coords["facecam"])
                        # If we found a refined layout or this is our first success, keep it
                        if not best_facecam or ts == 300:
                            best_facecam = refined
                            best_gameplay = coords["gameplay"]
                    if os.path.exists(shot): os.remove(shot)

            current_video_data["facecam"] = best_facecam
            current_video_data["gameplay"] = best_gameplay

            task_manager.update_task(task_id, "completed", 100, result={"clips": clips})
        except Exception as e:
            task_manager.update_task(task_id, "failed", error=str(e))

    threading.Thread(target=run).start()
    return jsonify({"task_id": task_id})

@app.route('/export', methods=['POST'])
def export():
    clip_data = request.json.get('clip')
    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id, "exporting", 0)

    def run():
        try:
            filename = f"clip_{int(clip_data['start'])}.mp4"
            out = get_module('editor').process_clip(
                current_video_data["path"],
                clip_data["start"], clip_data["end"],
                current_video_data["facecam"] or [0,0,300,300],
                current_video_data["gameplay"] or [0,0,1000,1000],
                filename,
                use_gpu=config.get('USE_GPU', False),
                transcript_words=current_video_data["words"]
            )
            task_manager.update_task(task_id, "completed", 100, result={"path": os.path.abspath(out)})
        except Exception as e:
            task_manager.update_task(task_id, "failed", error=str(e))

    threading.Thread(target=run).start()
    return jsonify({"task_id": task_id})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
