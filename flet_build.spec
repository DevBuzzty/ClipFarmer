# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

datas = []
binaries = []
hiddenimports = [
    'flet',
    'flet.canvas',
    'flet.charts',
    'flet.embed',
    'flet.map',
    'flet.video',
    'flet.webview',
    'google.genai',
    'moviepy',
    'yt_dlp',
    'PIL',
    'cv2',
    'numpy',
    'faster_whisper',
    'imageio',
    'decorator',
    'tqdm'
]

packages_to_collect = [
    'flet',
    'faster_whisper',
    'ctranslate2',
    'onnxruntime',
    'google.genai',
    'moviepy',
    'yt_dlp',
    'imageio',
    'decorator',
    'tqdm'
]

for package in packages_to_collect:
    try:
        tmp_ret = collect_all(package)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
        datas += copy_metadata(package)
    except Exception as e:
        print(f"Warning: Could not collect all for {package}: {e}")

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ViraFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to False for GUI apps
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ViraFlow',
)
