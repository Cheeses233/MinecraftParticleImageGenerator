# PyInstaller spec for a Windows single-file GUI executable.

from pathlib import Path

project_root = Path(SPECPATH).parent
icon_path = project_root / "resources" / "app_icon.ico"
version_path = project_root / "build" / "version_info.txt"

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(icon_path), "resources")],
    hiddenimports=[],
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
    name="ParticleGenerator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(icon_path),
    version=str(version_path),
)
