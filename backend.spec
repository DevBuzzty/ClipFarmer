# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['flask', 'flask_cors', 'requests', 'google.genai', 'dotenv', 'pydub', 'numpy', 'cv2']

# Collect all for complex packages
packages = ['faster_whisper', 'moviepy', 'flask', 'flask_cors', 'google.genai', 'requests', 'werkzeug', 'jinja2', 'itsdangerous', 'click', 'blinker', 'dotenv', 'PIL', 'cv2', 'yt_dlp']
for package in packages:
    try:
        tmp_ret = collect_all(package)
        datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
    except:
        pass


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
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
