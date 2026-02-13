# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

datas = []
binaries = []
hiddenimports = [
    'flask',
    'flask_cors',
    'google.genai',
    'moviepy',
    'yt_dlp',
    'PIL',
    'cv2',
    'numpy',
    'pydub'
]

# Collect everything from these specific complex/heavy packages
# We exclude standard flask/werkzeug from collect_all as it often interferes with hooks
packages_to_collect = [
    'faster_whisper',
    'ctranslate2',
    'onnxruntime',
    'google.genai',
    'moviepy',
    'yt_dlp'
]

for package in packages_to_collect:
    try:
        tmp_ret = collect_all(package)
        datas += tmp_ret[0]
        binaries += tmp_ret[1]
        hiddenimports += tmp_ret[2]
        # Metadata is important for some packages to identify versions
        datas += copy_metadata(package)
    except Exception as e:
        print(f"Warning: Could not collect all for {package}: {e}")

# Extra safety for Flask
hiddenimports += collect_submodules('flask')
hiddenimports += collect_submodules('flask_cors')
datas += copy_metadata('flask')

a = Analysis(
    ['backend/app.py'],
    pathex=['backend'],
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
