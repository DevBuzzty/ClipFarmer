from pydub import AudioSegment
import numpy as np

class AudioAnalyzer:
    def __init__(self, audio_path):
        self.audio_path = audio_path

    def get_hype_segments(self, window_ms=1000, threshold_sigma=2.0):
        """
        Identifiziert Segmente mit überdurchschnittlicher Lautstärke (Hype).
        """
        audio = AudioSegment.from_file(self.audio_path)

        # In chunks unterteilen und RMS berechnen
        rms_values = []
        for i in range(0, len(audio), window_ms):
            chunk = audio[i:i+window_ms]
            rms_values.append(chunk.rms)

        rms_array = np.array(rms_values)
        mean_rms = np.mean(rms_array)
        std_rms = np.std(rms_array)

        # Schwellenwert: Durchschnitt + X Standardabweichungen
        threshold = mean_rms + (threshold_sigma * std_rms)

        hype_indices = np.where(rms_array > threshold)[0]

        # Indizes in Zeitstempel (Sekunden) umwandeln
        hype_timestamps = []
        for idx in hype_indices:
            start_sec = (idx * window_ms) / 1000.0
            hype_timestamps.append(start_sec)

        # Benachbarte Zeitstempel zu Clustern zusammenfassen
        if not hype_timestamps:
            return []

        clusters = []
        if hype_timestamps:
            current_cluster = [hype_timestamps[0]]
            for i in range(1, len(hype_timestamps)):
                if hype_timestamps[i] - hype_timestamps[i-1] <= 5: # 5 Sek Lücke erlaubt
                    current_cluster.append(hype_timestamps[i])
                else:
                    clusters.append((current_cluster[0], current_cluster[-1]))
                    current_cluster = [hype_timestamps[i]]
            clusters.append((current_cluster[0], current_cluster[-1]))

        return clusters
