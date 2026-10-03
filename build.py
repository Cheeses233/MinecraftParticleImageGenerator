"""Build the Windows single-file application with its icon and version data."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parent
ICON_PATH = PROJECT_ROOT / "resources" / "app_icon.ico"
SPEC_PATH = PROJECT_ROOT / "build" / "ParticleGenerator.spec"
OUTPUT_PATH = PROJECT_ROOT / "build" / "dist" / "ParticleGenerator.exe"


def create_application_icon() -> None:
    """Generate a crisp app icon so no external artwork is required."""
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, 244, 244), radius=48, fill="#263b63")

    # A pixel-art particle cloud and a central bright particle.
    for x, y, color, radius in (
        (72, 82, "#55d6be", 12),
        (126, 61, "#9ff3df", 10),
        (181, 88, "#55d6be", 13),
        (59, 137, "#9ff3df", 10),
        (198, 145, "#9ff3df", 10),
        (83, 192, "#55d6be", 12),
        (157, 198, "#9ff3df", 11),
    ):
        draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=color)
    draw.rectangle((99, 91, 157, 149), fill="#f8d66d")
    draw.rectangle((111, 103, 145, 137), fill="#fff5c2")
    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        ICON_PATH,
        format="ICO",
        sizes=((16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)),
    )


def build() -> Path:
    """Run PyInstaller and return the finished standalone executable."""
    if not SPEC_PATH.is_file():
        raise FileNotFoundError(f"PyInstaller spec not found: {SPEC_PATH}")
    create_application_icon()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(OUTPUT_PATH.parent),
        "--workpath",
        str(PROJECT_ROOT / "build" / "work"),
        str(SPEC_PATH),
    ]
    print("Building standalone Windows executable...")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    if not OUTPUT_PATH.is_file():
        raise FileNotFoundError(
            f"PyInstaller completed without producing the expected executable: {OUTPUT_PATH}"
        )
    print(f"Build successful: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    try:
        build()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
