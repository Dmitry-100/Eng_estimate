# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
assets_root = project_root / "assets" / "windows"

datas = [
    (str(project_root / "templates"), "templates"),
    (str(project_root / "static"), "static"),
    (str(project_root / "Engineering Efficiency Measurement.xlsx"), "."),
]

hiddenimports = [
    "webview",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "webview.platforms.mshtml",
]

a = Analysis(
    ["desktop_app.py"],
    pathex=[str(project_root)],
    binaries=[],
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
    name="EngEstimate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(assets_root / "engestimate.ico"),
    version=str(assets_root / "version_info.txt"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
