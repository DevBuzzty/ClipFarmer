import flet as ft
import os
import json
import threading
import asyncio
import uuid
from downloader import Downloader
from transcriber import Transcriber
from analyzer import Analyzer
from editor import Editor
from audio_analyzer import AudioAnalyzer
from utils import extract_screenshot, refine_facecam_crop

# Theme Colors
BG_DARK = "#0b001a"
BG_PANEL = "#160033"
ACCENT_PURPLE = "#9d00ff"
ACCENT_PINK = "#ff00ff"
ACCENT_BLUE = "#00d4ff"
TEXT_MAIN = "#f0f0f5"
TEXT_DIM = "#a0a0b0"

class ViraFlowApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "ViraFlow v2.0 - AI Twitch Automator"
        self.page.bgcolor = BG_DARK
        self.page.padding = 0
        self.page.window.width = 1280
        self.page.window.height = 850

        self.config = self.load_config()
        self.current_video_data = {"path": None, "words": None, "facecam": None, "gameplay": None}
        self.modules = {}

        self.init_ui()

    def load_config(self):
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    return json.load(f)
            except: pass
        return {
            "GEMINI_API_KEY": os.getenv('GEMINI_API_KEY', ''),
            "WHISPER_MODEL": "base",
            "USE_GPU": False,
            "LAYOUT": "stack",
            "CAPTIONS": True
        }

    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f)
        self.modules = {} # Reset modules to apply new config

    def get_module(self, name):
        if name not in self.modules:
            if name == 'downloader': self.modules[name] = Downloader()
            elif name == 'transcriber':
                self.modules[name] = Transcriber(model_size=self.config.get('WHISPER_MODEL', 'base'),
                                           device="cuda" if self.config.get('USE_GPU') else "cpu")
            elif name == 'analyzer':
                self.modules[name] = Analyzer(api_key=self.config.get('GEMINI_API_KEY'))
            elif name == 'editor':
                self.modules[name] = Editor(layout=self.config.get('LAYOUT', 'stack'),
                                       show_captions=self.config.get('CAPTIONS', True))
        return self.modules.get(name)

    def init_ui(self):
        # Header
        header = ft.Container(
            content=ft.Row([
                ft.Text("VIRAFLOW", size=24, weight="bold", color=ACCENT_BLUE),
                ft.Row([
                    ft.TextButton("ANALYSE", on_click=lambda _: self.switch_view("analyze"), style=ft.ButtonStyle(color=TEXT_MAIN)),
                    ft.TextButton("EINSTELLUNGEN", on_click=lambda _: self.switch_view("settings"), style=ft.ButtonStyle(color=TEXT_MAIN)),
                ], spacing=20)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(30),
            border=ft.border.only(bottom=ft.BorderSide(1, "white10"))
        )

        # Analyze View
        self.url_input = ft.TextField(
            label="Twitch VOD URL",
            border_color=ACCENT_BLUE,
            focused_border_color=ACCENT_PINK,
            color=TEXT_MAIN,
            label_style=ft.TextStyle(color=TEXT_DIM),
            expand=True
        )

        self.analyze_btn = ft.ElevatedButton(
            "START ANALYSE",
            color=TEXT_MAIN,
            bgcolor=ACCENT_PURPLE,
            height=50,
            on_click=self.start_analysis_task
        )

        self.progress_ring = ft.ProgressRing(visible=False, color=ACCENT_PINK)
        self.progress_status = ft.Text("", color=TEXT_DIM)

        self.clip_grid = ft.ResponsiveRow(spacing=20, run_spacing=20)

        self.analyze_view = ft.Container(
            content=ft.Column([
                ft.Row([self.url_input, self.analyze_btn], spacing=10),
                ft.Row([self.progress_ring, self.progress_status], alignment="center", spacing=10),
                ft.Divider(color="white10"),
                self.clip_grid
            ], scroll=ft.ScrollMode.AUTO),
            padding=40,
            expand=True,
            visible=True
        )

        # Settings View
        self.gemini_key_input = ft.TextField(label="Gemini API Key", value=self.config['GEMINI_API_KEY'], password=True, can_reveal_password=True)
        self.whisper_dropdown = ft.Dropdown(
            label="Whisper Modell",
            value=self.config['WHISPER_MODEL'],
            options=[
                ft.dropdown.Option("tiny"),
                ft.dropdown.Option("base"),
                ft.dropdown.Option("small"),
            ]
        )
        self.layout_dropdown = ft.Dropdown(
            label="Export Layout",
            value=self.config['LAYOUT'],
            options=[
                ft.dropdown.Option("stack", "Stack (Facecam oben)"),
                ft.dropdown.Option("overlay", "Overlay (Facecam klein)"),
            ]
        )
        self.gpu_switch = ft.Switch(label="GPU Beschleunigung (CUDA)", value=self.config['USE_GPU'])
        self.captions_switch = ft.Switch(label="Automatische Untertitel", value=self.config['CAPTIONS'])

        self.settings_view = ft.Container(
            content=ft.Column([
                ft.Text("Konfiguration", size=30, weight="bold", color=ACCENT_BLUE),
                self.gemini_key_input,
                self.whisper_dropdown,
                self.layout_dropdown,
                self.gpu_switch,
                self.captions_switch,
                ft.ElevatedButton("SPEICHERN", on_click=self.save_settings, bgcolor=ACCENT_PURPLE, color=TEXT_MAIN)
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            padding=40,
            expand=True,
            visible=False
        )

        self.main_content = ft.Stack([self.analyze_view, self.settings_view], expand=True)

        self.page.add(
            ft.Container(
                content=ft.Column([
                    header,
                    self.main_content
                ], expand=True),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[BG_DARK, BG_PANEL, "#2a004f"]
                ),
                expand=True
            )
        )

    def switch_view(self, view_name):
        self.analyze_view.visible = (view_name == "analyze")
        self.settings_view.visible = (view_name == "settings")
        self.page.update()

    def save_settings(self, e):
        self.config['GEMINI_API_KEY'] = self.gemini_key_input.value
        self.config['WHISPER_MODEL'] = self.whisper_dropdown.value
        self.config['LAYOUT'] = self.layout_dropdown.value
        self.config['USE_GPU'] = self.gpu_switch.value
        self.config['CAPTIONS'] = self.captions_switch.value
        self.save_config()
        self.page.snack_bar = ft.SnackBar(ft.Text("Einstellungen gespeichert!"))
        self.page.snack_bar.open = True
        self.page.update()

    def update_status(self, text, busy=True):
        self.progress_status.value = text
        self.progress_ring.visible = busy
        self.analyze_btn.disabled = busy
        self.page.update()

    def start_analysis_task(self, e):
        url = self.url_input.value
        if not url: return
        threading.Thread(target=self.run_analysis, args=(url,), daemon=True).start()

    def run_analysis(self, url):
        try:
            self.update_status("Lade VOD herunter...")
            path = self.get_module('downloader').download_video(url)
            self.current_video_data["path"] = path

            self.update_status("KI Transkription...")
            audio = self.get_module('downloader').extract_audio(path)
            res = self.get_module('transcriber').transcribe(audio)
            self.current_video_data["words"] = res["words"]

            self.update_status("Audio-Analyse...")
            aa = AudioAnalyzer(audio)
            hype = aa.get_hype_segments()

            self.update_status("KI sucht virale Momente...")
            clips = self.get_module('analyzer').find_viral_clips(res, hype)

            self.update_status("Facecam wird lokalisiert...")
            best_facecam = None
            best_gameplay = None
            for ts in [300, 600, 900]:
                shot = f"temp_shot_{ts}.jpg"
                if extract_screenshot(path, ts, shot):
                    coords = self.get_module('analyzer').detect_facecam(shot)
                    if coords:
                        refined = refine_facecam_crop(shot, coords["facecam"])
                        if not best_facecam or ts == 300:
                            best_facecam = refined
                            best_gameplay = coords["gameplay"]
                    if os.path.exists(shot): os.remove(shot)

            self.current_video_data["facecam"] = best_facecam
            self.current_video_data["gameplay"] = best_gameplay

            # Display Clips
            self.page.run_task(self.display_clips, clips, url)
            self.update_status("Fertig!", busy=False)

        except Exception as err:
            self.update_status(f"Fehler: {err}", busy=False)

    async def display_clips(self, clips, url):
        self.clip_grid.controls.clear()
        for clip in clips:
            # Generate Twitch URL
            start_sec = int(clip['start'])
            h, m, s = start_sec // 3600, (start_sec % 3600) // 60, start_sec % 60
            twitch_url = f"{url}?t={h}h{m}m{s}s"

            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(ft.Text(f"Viral: {clip['rating']}/10", size=10, weight="bold", color="black"),
                                     bgcolor=ACCENT_BLUE, padding=5, border_radius=5),
                        ft.Text(f"{int(clip['start'])}s - {int(clip['end'])}s", size=10, color=TEXT_DIM)
                    ], alignment="spaceBetween"),
                    ft.Text(clip['title'], weight="bold", size=14, color=TEXT_MAIN),
                    ft.Text(clip['description'], size=12, color=TEXT_DIM, max_lines=2),
                    ft.Row([
                        ft.OutlinedButton("LINK", on_click=lambda _, u=twitch_url: self.page.launch_url(u), expand=1),
                        ft.ElevatedButton("EXPORT", on_click=lambda _, c=clip: self.start_export(c), bgcolor=ACCENT_PURPLE, color=TEXT_MAIN, expand=1),
                        ft.IconButton(ft.icons.UPLOAD, on_click=lambda _: self.show_upload_info(), icon_color=ACCENT_BLUE)
                    ])
                ]),
                padding=20,
                bgcolor=ft.colors.with_opacity(ft.colors.WHITE, 0.1),
                border=ft.border.all(1, "white10"),
                border_radius=15,
                col={"sm": 12, "md": 6, "lg": 4}
            )
            self.clip_grid.controls.append(card)
        self.page.update()

    def start_export(self, clip_data):
        threading.Thread(target=self.run_export, args=(clip_data,), daemon=True).start()

    def show_upload_info(self):
        self.page.snack_bar = ft.SnackBar(ft.Text("Upload-Integration erfordert eigene API-Secrets (YouTube/TikTok). Siehe README."))
        self.page.snack_bar.open = True
        self.page.update()

    def run_export(self, clip_data):
        try:
            self.update_status(f"Exportiere Clip: {clip_data['title']}...")
            filename = f"clip_{int(clip_data['start'])}.mp4"
            out = self.get_module('editor').process_clip(
                self.current_video_data["path"],
                clip_data["start"], clip_data["end"],
                self.current_video_data["facecam"] or [0,0,300,300],
                self.current_video_data["gameplay"] or [0,0,1000,1000],
                filename,
                use_gpu=self.config.get('USE_GPU', False),
                transcript_words=self.current_video_data["words"]
            )
            self.update_status(f"Gespeichert: {filename}", busy=False)
        except Exception as err:
            self.update_status(f"Export Fehler: {err}", busy=False)

if __name__ == "__main__":
    ft.app(target=ViraFlowApp)
