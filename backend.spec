# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'flask',
    'flask_cors',
    'requests',
    'google.genai',
    'dotenv',
    'pydub',
    'numpy',
    'cv2',
    'werkzeug',
    'jinja2',
    'itsdangerous',
    'click',
    'blinker',
    'moviepy'
]

# Collect everything from these complex packages
packages = [
    'faster_whisper',
    'moviepy',
    'flask',
    'flask_cors',
    'google.genai',
    'requests',
    'werkzeug',
    'jinja2',
    'itsdangerous',
    'click',
    'blinker',
    'dotenv',
    'PIL',
    'cv2',
    'yt_dlp'
]

for package in packages:
    try:
        tmp_ret = collect_all(package)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
    except Exception as e:
        print(f"Warning: Could not collect all for {package}: {e}")

a = Analysis(
    ['backend/app.py'],
    pathex=[],
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
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
