import google.generativeai as genai
import os
import json
from PIL import Image

class Analyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def find_viral_clips(self, transcript_data):
        # transcript_data is the dict from Transcriber
        prompt = f"""
        Analyze the following transcript from a Twitch stream and identify the most viral, funny, or high-energy moments.
        For each moment, provide:
        1. Start and end timestamps (in seconds). Clips should be between 15 and 60 seconds.
        2. A short description of why it's viral.
        3. A virality rating from 1 to 10.
        4. A catchy title for the clip.

        Transcript:
        {transcript_data['text']}

        Return the result strictly as a JSON list of objects:
        [
            {{"start": 10.5, "end": 40.5, "description": "...", "rating": 9, "title": "..."}},
            ...
        ]
        """

        response = self.model.generate_content(prompt)
        # Extract JSON from response
        try:
            # Gemini often wraps JSON in code blocks
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
        # Load image
        img = Image.open(screenshot_path)

        prompt = """
        Look at this screenshot from a Twitch stream.
        Identify the bounding box of the facecam (the area showing the streamer's face).
        Identify the bounding box of the main gameplay area.
        Return the coordinates as a JSON object with 'facecam' and 'gameplay' keys, each containing [ymin, xmin, ymax, xmax] in normalized coordinates (0-1000).

        Format:
        {
            "facecam": [ymin, xmin, ymax, xmax],
            "gameplay": [ymin, xmin, ymax, xmax]
        }
        """

        response = self.model.generate_content([prompt, img])

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
            # Default fallback: assume facecam is top left or right?
            # Better to return None and handle it.
            return None
