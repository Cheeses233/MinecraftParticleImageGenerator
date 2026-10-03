"""Interfaces shared by Minecraft version-specific datapack adapters."""

from __future__ import annotations

from abc import ABC
from typing import Any


class MinecraftVersionAdapter(ABC):
    """Provides version-dependent datapack metadata and command syntax."""

    version_name: str
    pack_format: int
    function_directory = "function"

    def pack_description(self) -> str:
        """Return the description embedded in pack.mcmeta."""
        return f"Particle image generated for Minecraft {self.version_name}"

    def pack_metadata(self) -> dict[str, Any]:
        """Return version-correct metadata for the datapack root file."""
        return {
            "pack": {
                "pack_format": self.pack_format,
                "description": self.pack_description(),
            }
        }
