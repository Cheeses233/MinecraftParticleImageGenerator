"""Registry of explicitly supported Minecraft Java Edition versions."""

from __future__ import annotations

from version.base import MinecraftVersionAdapter
from version.mc1204 import Minecraft1204Adapter
from version.mc1205 import Minecraft1205Adapter
from version.mc121x import Minecraft121xAdapter


_VERSION_FORMATS = {
    "1.21": 48,
    "1.21.1": 48,
    "1.21.2": 57,
    "1.21.3": 57,
    "1.21.4": 61,
    "1.21.5": 71,
    "1.21.6": 80,
    "1.21.7": 81,
    "1.21.8": 81,
    "1.21.9": 88,
    "1.21.10": 88,
    "1.21.11": 94,
}

SUPPORTED_VERSIONS = (
    "1.20.4",
    "1.20.5",
    "1.20.6",
    *_VERSION_FORMATS.keys(),
)


def create_adapter(version_name: str) -> MinecraftVersionAdapter:
    """Return an adapter for a supported version or raise a clear error."""
    if version_name == "1.20.4":
        return Minecraft1204Adapter()
    if version_name in {"1.20.5", "1.20.6"}:
        return Minecraft1205Adapter(version_name)

    pack_format = _VERSION_FORMATS.get(version_name)
    if pack_format is None:
        raise ValueError(f"暂不支持 Minecraft Java Edition {version_name}。")
    return Minecraft121xAdapter(
        version_name,
        pack_format,
        modern_metadata=version_name in {"1.21.9", "1.21.10", "1.21.11"},
    )
