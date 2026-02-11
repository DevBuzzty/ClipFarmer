from faster_whisper import WhisperModel
import os

class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        # device can be "cuda" if GPU is available.
        # Optimization: use multiple threads for CPU
        num_workers = 4 if device == "cpu" else 1
        cpu_threads = 4 if device == "cpu" else 0
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            num_workers=num_workers,
            cpu_threads=cpu_threads
        )

    def transcribe(self, audio_path):
        segments, info = self.model.transcribe(audio_path, beam_size=5, word_timestamps=True)

        full_transcript = []
        words_list = []

        for segment in segments:
            full_transcript.append(segment.text)
            for word in segment.words:
                words_list.append({
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "probability": word.probability
                })

        return {
            "text": "".join(full_transcript),
            "words": words_list,
            "language": info.language
        }
