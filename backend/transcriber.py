from faster_whisper import WhisperModel
import os

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path):
        segments, info = self.model.transcribe(audio_path, beam_size=5, word_timestamps=True)

        full_text = ""
        words = []

        for segment in segments:
            full_text += segment.text + " "
            for word in segment.words:
                words.append({
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability
                })

        return {
            "text": full_text.strip(),
            "words": words,
            "language": info.language
        }
