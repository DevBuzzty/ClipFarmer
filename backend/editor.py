from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, TextClip
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

        target_w = 1080
        target_h = 1920

        face_w = target_w
        face_h = int(target_w / (16/9))

        game_w = target_w
        game_h = target_h - face_h

        vw, vh = video.size
        fy1, fx1, fy2, fx2 = [c * vh / 1000 if i % 2 == 0 else c * vw / 1000 for i, c in enumerate(facecam_coords)]

        face_source = video.crop(x1=fx1, y1=fy1, x2=fx2, y2=fy2)
        face_aspect = 16/9
        if face_source.w / face_source.h > face_aspect:
            new_w = face_source.h * face_aspect
            face_source = face_source.crop(x_center=face_source.w/2, width=new_w)
        else:
            new_h = face_source.w / face_aspect
            face_source = face_source.crop(y_center=face_source.h/2, height=new_h)

        face_clip = face_source.resize(width=face_w, height=face_h)

        gy1, gx1, gy2, gx2 = [c * vh / 1000 if i % 2 == 0 else c * vw / 1000 for i, c in enumerate(gameplay_coords)]
        game_source = video.crop(x1=gx1, y1=gy1, x2=gx2, y2=gy2)

        scale_w = target_w / game_source.w
        scale_h = (target_h if self.layout == 'overlay' else game_h) / game_source.h
        scale = max(scale_w, scale_h)

        game_clip = game_source.resize(scale).crop(
            x_center=game_source.w * scale / 2,
            y_center=game_source.h * scale / 2,
            width=target_w,
            height=(target_h if self.layout == 'overlay' else game_h)
        )

        caption_clips = []
        if self.show_captions and transcript_words:
            caption_clips = self._generate_caption_clips(transcript_words, start_time, end_time, target_w, target_h)

        if self.layout == 'overlay':
            face_small = face_clip.resize(width=target_w * 0.35)
            face_small = face_small.set_position((target_w - face_small.w - 40, 40))
            final_video = CompositeVideoClip([game_clip, face_small] + caption_clips, size=(target_w, target_h))
        else:
            final_video = CompositeVideoClip([
                face_clip.set_position(("center", 0)),
                game_clip.set_position(("center", face_h))
            ] + caption_clips, size=(target_w, target_h))

        output_path = os.path.join(self.output_dir, output_filename)
        codec = "h264_nvenc" if use_gpu else "libx264"

        write_args = {
            "codec": codec,
            "audio_codec": "aac",
            "fps": video.fps,
            "threads": 4,
            "logger": None
        }

        try:
            final_video.write_videofile(output_path, **{k: v for k, v in write_args.items() if v is not None})
        except:
            write_args["codec"] = "libx264"
            final_video.write_videofile(output_path, **{k: v for k, v in write_args.items() if v is not None})

        video.close()
        face_source.close()
        game_source.close()
        final_video.close()
        return output_path

    def _generate_caption_clips(self, words, start_time, end_time, vw, vh):
        clips = []
        sub_words = [w for w in words if w['start'] >= start_time and w['end'] <= end_time]

        phrase_size = 3
        for i in range(0, len(sub_words), phrase_size):
            phrase = sub_words[i:i+phrase_size]
            text = " ".join([w['word'].strip() for w in phrase]).upper()
            p_start = phrase[0]['start'] - start_time
            p_end = phrase[-1]['end'] - start_time

            img = self._create_text_image(text, vw, 240)

            caption = (ImageClip(np.array(img))
                       .set_start(p_start)
                       .set_duration(p_end - p_start)
                       .set_position(("center", int(vh * 0.75))))

            # Pop-in animation
            duration = p_end - p_start
            if duration > 0.2:
                caption = caption.resize(lambda t: 0.8 + 0.4*(t/0.1) if t<0.1 else 1.2 - 0.2*((t-0.1)/0.1) if t<0.2 else 1.0)

            clips.append(caption)
        return clips

    def _create_text_image(self, text, width, height):
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arialbd.ttf", 70)
        except:
            font = ImageFont.load_default()

        w, h = draw.textbbox((0, 0), text, font=font)[2:]
        draw.text(((width-w)/2 + 5, (height-h)/2 + 5), text, font=font, fill="black")
        # Purple/Neon Pink theme for captions
        draw.text(((width-w)/2, (height-h)/2), text, font=font, fill="#ff00ff")
        return img
