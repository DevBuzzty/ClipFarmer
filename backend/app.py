import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from downloader import Downloader
from transcriber import Transcriber
from analyzer import Analyzer
from editor import Editor
from utils import extract_screenshot

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize modules
downloader = Downloader()
transcriber = Transcriber(model_size="base") # Use base for testing, user can change to medium/large
analyzer = Analyzer(api_key=os.getenv('GEMINI_API_KEY'))
editor = Editor()

# Global state to keep track of current video info
current_video = {
    "path": None,
    "facecam_coords": None,
    "gameplay_coords": None
}

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
            output_filename
        )

        return jsonify({"success": True, "path": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
