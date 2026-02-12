from pydub import AudioSegment
import numpy as np

class AudioAnalyzer:
    def __init__(self, audio_path):
        self.audio = AudioSegment.from_file(audio_path)

    def get_hype_segments(self, threshold_db=-20, min_duration_sec=2, chunk_size_ms=500):
        # Convert to mono and get raw data
        mono_audio = self.audio.set_channels(1)
        samples = np.array(mono_audio.get_array_of_samples())

        # Calculate RMS in chunks
        chunk_samples = int((chunk_size_ms / 1000.0) * mono_audio.frame_rate)
        rms_values = []

        for i in range(0, len(samples), chunk_samples):
            chunk = samples[i:i+chunk_samples]
            if len(chunk) == 0: continue
            rms = np.sqrt(np.mean(chunk**2))
            # Convert to dBFS
            if rms > 0:
                db = 20 * np.log10(rms / (2**15)) # Assumes 16-bit
            else:
                db = -100
            rms_values.append(db)

        # Find segments above threshold
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

        return hype_ranges
