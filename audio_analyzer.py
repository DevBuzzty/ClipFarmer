from moviepy.editor import AudioFileClip
import numpy as np

class AudioAnalyzer:
    def __init__(self, audio_path):
        """
        Initialisiert den AudioAnalyzer ohne pydub (Python 3.13+ kompatibel).
        Nutzt moviepy und numpy zur RMS-Berechnung.
        """
        self.clip = AudioFileClip(audio_path)
        self.fps = self.clip.fps
        # Lade die Audiodaten als Numpy-Array (Werte zwischen -1.0 und 1.0)
        self.samples = self.clip.to_soundarray()
        if len(self.samples.shape) > 1:
            # Zu Mono konvertieren (Mittelwert der Kanäle)
            self.samples = np.mean(self.samples, axis=1)

    def get_hype_segments(self, threshold_db=-20, min_duration_sec=2, chunk_size_ms=500):
        chunk_samples = int((chunk_size_ms / 1000.0) * self.fps)
        rms_values = []

        for i in range(0, len(self.samples), chunk_samples):
            chunk = self.samples[i:i+chunk_samples]
            if len(chunk) == 0: continue

            # RMS Berechnung
            rms = np.sqrt(np.mean(chunk**2))

            # Umrechnung in dB (0 dB ist Maximum bei moviepy floats)
            if rms > 0:
                db = 20 * np.log10(rms)
            else:
                db = -100
            rms_values.append(db)

        hype_ranges = []
        start_idx = None

        for i, db in enumerate(rms_values):
            if db > threshold_db:
                if start_idx is None:
                    start_idx = i
            else:
                if start_idx is not None:
                    duration = (i - start_idx) * (chunk_size_ms / 1000.0)
                    if duration >= min_duration_sec:
                        hype_ranges.append((start_idx * chunk_size_ms / 1000.0, i * chunk_size_ms / 1000.0))
                    start_idx = None

        # Clip schließen um Ressourcen freizugeben
        self.clip.close()
        return hype_ranges
