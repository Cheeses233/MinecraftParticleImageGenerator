"""Resolve bundled and development-time resource paths consistently."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Return an absolute path to a resource in source or PyInstaller mode."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        root = Path(bundle_root)
    else:
        root = Path(__file__).resolve().parent.parent
    return root / relative_path


def check_required_resources() -> tuple[Path, ...]:
    """Verify the packaged resources the application requires at startup."""
    required = (resource_path("resources/app_icon.ico"),)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "缺少必需的软件资源文件：\n" + "\n".join(missing)
        )
    return required
