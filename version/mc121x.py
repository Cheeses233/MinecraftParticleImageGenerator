"""Adapters for Minecraft Java Edition 1.21 releases."""

from __future__ import annotations

from typing import Any

from version.mc1204 import Minecraft1204Adapter


class Minecraft121xAdapter(Minecraft1204Adapter):
    """Shared command syntax and folder layout for the 1.21 release line."""

    def __init__(
        self,
        version_name: str,
        pack_format: int,
        *,
        modern_metadata: bool = False,
    ) -> None:
        self.version_name = version_name
        self.pack_format = pack_format
        self.modern_metadata = modern_metadata

    def pack_metadata(self) -> dict[str, Any]:
        if self.modern_metadata:
            data_version = [self.pack_format, 0]
            return {
                "pack": {
                    "description": self.pack_description(),
                    "min_format": data_version,
                    "max_format": data_version,
                }
            }
        return super().pack_metadata()
