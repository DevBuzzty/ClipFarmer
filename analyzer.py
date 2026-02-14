from google import genai
import os
import json
from PIL import Image

class Analyzer:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-1.5-pro'

    def find_viral_clips(self, transcript_data, hype_segments=None):
        hype_info = ""
        if hype_segments:
            hype_info = f"\nZusätzliche Info: Die folgenden Zeitbereiche hatten hohe Audio-Energie (Lachen, Schreien, Hype): {hype_segments}\n"

        prompt = f"""
        Analysiere das folgende Transkript eines Twitch-Streams und identifiziere die viralsten, lustigsten oder energiegeladensten Momente.
        {hype_info}
        Für jeden Moment gib an:
        1. Start- und End-Timestamps (in Sekunden). Clips sollten zwischen 15 und 60 Sekunden lang sein.
        2. Eine kurze Beschreibung, warum es viral ist.
        3. Ein Virality-Rating von 1 bis 10.
        4. Einen packenden Titel für den Clip.
        5. Eine SEO-optimierte Beschreibung für YouTube/TikTok.
        6. Eine Liste von 5 relevanten Hashtags.

        Transkript:
        {transcript_data['text']}

        Gib das Ergebnis strikt als JSON-Liste von Objekten zurück:
        [
            {{"start": 10.5, "end": 40.5, "description": "...", "rating": 9, "title": "...", "seo_description": "...", "hashtags": ["#tag1", ...]}},
            ...
        ]
        Anforderungen:
        - Nutze die Audio-Hype-Daten, um den Höhepunkt des Moments exakt zu erfassen.
        - Achte darauf, dass der Kontext (Vorbereitung eines Witzes) mit im Clip ist.
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )

        try:
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            clips = json.loads(text.strip())
            return clips
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return []

    def detect_facecam(self, screenshot_path):
        img = Image.open(screenshot_path)

        prompt = """
        Analysiere diesen Screenshot eines Twitch-Streams.
        Identifiziere das Bounding-Box des Facecam-Bereichs (wo der Streamer zu sehen ist).
        Identifiziere das Bounding-Box des Gameplay-Bereichs.
        Gib die Koordinaten als JSON-Objekt zurück mit 'facecam' und 'gameplay' Keys.
        Jeder Key enthält [ymin, xmin, ymax, xmax] in normalisierten Koordinaten (0-1000).

        Format:
        {
            "facecam": [ymin, xmin, ymax, xmax],
            "gameplay": [ymin, xmin, ymax, xmax]
        }
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt, img]
        )

        try:
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            coords = json.loads(text.strip())
            return coords
        except Exception as e:
            print(f"Error parsing Gemini facecam response: {e}")
            return None
