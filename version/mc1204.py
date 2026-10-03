"""Minecraft Java Edition 1.20.4 command and datapack adapter."""

from __future__ import annotations

from version.base import MinecraftVersionAdapter


class Minecraft1204Adapter(MinecraftVersionAdapter):
    """Adapter for Java Edition 1.20.4 (datapack format 26)."""

    version_name = "1.20.4"
    pack_format = 26
