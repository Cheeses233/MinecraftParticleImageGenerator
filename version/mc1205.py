"""Minecraft Java Edition 1.20.5 and 1.20.6 datapack adapter."""

from __future__ import annotations

from version.mc1204 import Minecraft1204Adapter


class Minecraft1205Adapter(Minecraft1204Adapter):
    """Adapter for Java Edition 1.20.5/1.20.6 (datapack format 41)."""

    pack_format = 41

    def __init__(self, version_name: str = "1.20.5") -> None:
        self.version_name = version_name
