from moviepy.editor import VideoFileClip, clips_array, vfx, CompositeVideoClip, ImageClip
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class Editor:
    def __init__(self, output_dir='clips', layout='stack', show_captions=True):
        self.output_dir = output_dir
        self.layout = layout
        self.show_captions = show_captions
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_clip(self, video_path, start_time, end_time, facecam_coords, gameplay_coords, output_filename, use_gpu=False, transcript_words=None):
        video = VideoFileClip(video_path).subclip(start_time, end_time)

        # Target: 9:16 (e.g., 1080x1920)
        target_w = 1080
        target_h = 1920

        # Facecam (16:9) -> 1080x608
        face_w = target_w
        face_h = int(target_w / (16/9))

        # Gameplay area
        game_w = target_w
        game_h = target_h - face_h # 1312

        # Extract Facecam
        # facecam_coords: [ymin, xmin, ymax, xmax] in 0-1000
        vw, vh = video.size
        fy1, fx1, fy2, fx2 = [c * vh / 1000 if i % 2 == 0 else c * vw / 1000 for i, c in enumerate(facecam_coords)]

        face_source = video.crop(x1=fx1, y1=fy1, x2=fx2, y2=fy2)
        # Ensure facecam is 16:9 before resizing to face_w x face_h
        face_aspect = 16/9
        if face_source.w / face_source.h > face_aspect:
            # Too wide
            new_w = face_source.h * face_aspect
            face_source = face_source.crop(x_center=face_source.w/2, width=new_w)
        else:
            # Too tall
            new_h = face_source.w / face_aspect
            face_source = face_source.crop(y_center=face_source.h/2, height=new_h)

        face_clip = face_source.resize(width=face_w, height=face_h)

        # Extract Gameplay (Centered crop to fill 1080x1312)
        # We take the center of the gameplay area identified or just center of the whole video if gameplay_coords is too small
        # Actually, let's use the provided gameplay_coords if they exist, but ensure we crop it to the right aspect ratio.

        # For simplicity, if we want to fill game_w x game_h (1080x1312):
        # The aspect ratio is 1080/1312 = 0.823
        # Original gameplay area might be different.

        gy1, gx1, gy2, gx2 = [c * vh / 1000 if i % 2 == 0 else c * vw / 1000 for i, c in enumerate(gameplay_coords)]
        game_source = video.crop(x1=gx1, y1=gy1, x2=gx2, y2=gy2)

        # Resize game_source to fill game_w x game_h
        # To avoid black bars, we scale so the smaller dimension fits and then crop the larger dimension

        # Calculate scaling factor
        scale_w = game_w / game_source.w
        scale_h = game_h / game_source.h
        scale = max(scale_w, scale_h)

        game_clip = game_source.resize(scale).crop(
            x_center=game_source.w * scale / 2,
            y_center=game_source.h * scale / 2,
            width=game_w,
            height=game_h
        )

        # Generate Captions
        caption_clips = []
        if self.show_captions and transcript_words:
            caption_clips = self._generate_caption_clips(transcript_words, start_time, end_time, target_w, target_h)

        # Combine
        if self.layout == 'overlay':
            # Overlay: Gameplay is full background, facecam is small in corner
            face_small = face_clip.resize(width=target_w * 0.35)
            # Add a small margin and position at top right
            face_small = face_small.set_position((target_w - face_small.w - 40, 40))

            # Re-crop gameplay to fill 9:16 completely
            game_full = game_source.resize(height=target_h).crop(x_center=game_source.w * (target_h/game_source.h) / 2, width=target_w)

            final_video = CompositeVideoClip([
                game_full,
                face_small
            ] + caption_clips, size=(target_w, target_h))
        else:
            # Default: Stacked
            final_video = CompositeVideoClip([
                face_clip.set_position(("center", 0)),
                game_clip.set_position(("center", face_h))
            ] + caption_clips, size=(target_w, target_h))

        output_path = os.path.join(self.output_dir, output_filename)
        codec = "h264_nvenc" if use_gpu else "libx264"

        # Optimization: use more threads and a faster preset
        write_args = {
            "codec": codec,
            "audio_codec": "aac",
            "fps": video.fps,
            "threads": 4,
            "preset": "ultrafast" if not use_gpu else None, # nvenc doesn't use 'preset' the same way
            "logger": None # Disable moviepy logging for performance
        }

        try:
            final_video.write_videofile(output_path, **{k: v for k, v in write_args.items() if v is not None})
        except:
            # Fallback to cpu
            write_args["codec"] = "libx264"
            write_args["preset"] = "ultrafast"
            final_video.write_videofile(output_path, **{k: v for k, v in write_args.items() if v is not None})

        # Memory cleanup
        video.close()
        face_source.close()
        game_source.close()
        final_video.close()

        return output_path

    def _generate_caption_clips(self, words, start_time, end_time, vw, vh):
        clips = []
        # Filter words in this subclip
        sub_words = [w for w in words if w['start'] >= start_time and w['end'] <= end_time]

        # Group words into short phrases (e.g., 3-5 words)
        phrase_size = 3
        for i in range(0, len(sub_words), phrase_size):
            phrase = sub_words[i:i+phrase_size]
            text = " ".join([w['word'].strip() for w in phrase]).upper()
            p_start = phrase[0]['start'] - start_time
            p_end = phrase[-1]['end'] - start_time

            # Create an image for the text
            img = self._create_text_image(text, vw, 200)

            caption = (ImageClip(np.array(img))
                       .set_start(p_start)
                       .set_duration(p_end - p_start)
                       .set_position(("center", int(vh * 0.8)))) # Bottom area

            # Subtle Pop-In Animation
            duration = p_end - p_start
            if duration > 0.3:
                caption = caption.resize(lambda t: 0.8 + 0.4 * (t/0.1) if t < 0.1 else 1.2 - 0.2 * ((t-0.1)/0.1) if t < 0.2 else 1.0)

            clips.append(caption)

        return clips

    def _create_text_image(self, text, width, height):
        # Create transparent image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Try to load a bold font
        try:
            font = ImageFont.truetype("arialbd.ttf", 60)
        except:
            font = ImageFont.load_default()

        # Get text size
        w, h = draw.textbbox((0, 0), text, font=font)[2:]

        # Draw shadow
        draw.text(((width-w)/2 + 4, (height-h)/2 + 4), text, font=font, fill="black")
        # Draw main text (Yellow for viral look)
        draw.text(((width-w)/2, (height-h)/2), text, font=font, fill="#FFD700")

        return img
