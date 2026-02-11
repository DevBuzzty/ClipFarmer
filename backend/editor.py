from moviepy.editor import VideoFileClip, clips_array, vfx, CompositeVideoClip
import os

class Editor:
    def __init__(self, output_dir='clips'):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_clip(self, video_path, start_time, end_time, facecam_coords, gameplay_coords, output_filename, use_gpu=False):
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

        # Combine
        final_video = CompositeVideoClip([
            face_clip.set_position(("center", 0)),
            game_clip.set_position(("center", face_h))
        ], size=(target_w, target_h))

        output_path = os.path.join(self.output_dir, output_filename)
        codec = "h264_nvenc" if use_gpu else "libx264"
        try:
            final_video.write_videofile(output_path, codec=codec, audio_codec="aac", fps=video.fps)
        except:
            # Fallback to cpu
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=video.fps)

        return output_path
