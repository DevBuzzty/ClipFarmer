import yt_dlp
import os

class Downloader:
    def __init__(self, download_dir='downloads'):
        self.download_dir = download_dir
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    def download_video(self, url, progress_hooks=None):
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'progress_hooks': progress_hooks or [],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    def extract_audio(self, video_path):
        audio_path = os.path.splitext(video_path)[0] + '.wav'
        # We can use moviepy or ffmpeg directly. Since moviepy is a dependency, let's use it or just yt-dlp to extract audio.
        # Actually, let's use ffmpeg via command line for speed if available, or moviepy.
        import subprocess
        command = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            audio_path, '-y'
        ]
        subprocess.run(command, check=True)
        return audio_path
