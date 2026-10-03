"""Regression tests for supported Minecraft datapack layouts."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from core.datapack_builder import DatapackBuilder
from version.registry import SUPPORTED_VERSIONS, create_adapter


class VersionExportTests(unittest.TestCase):
    def test_all_supported_versions_use_function_directory(self) -> None:
        for version_name in SUPPORTED_VERSIONS:
            with self.subTest(version=version_name):
                adapter = create_adapter(version_name)
                self.assertEqual(adapter.function_directory, "function")

    def test_1219_uses_modern_pack_metadata(self) -> None:
        metadata = create_adapter("1.21.9").pack_metadata()["pack"]
        self.assertEqual(metadata["min_format"], [88, 0])
        self.assertEqual(metadata["max_format"], [88, 0])
        self.assertNotIn("pack_format", metadata)

    def test_zip_layout_and_metadata_follow_selected_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for version_name, format_key, format_value in (
                ("1.20.4", "pack_format", 26),
                ("1.20.6", "pack_format", 41),
                ("1.21.8", "pack_format", 81),
                ("1.21.11", "min_format", [94, 0]),
            ):
                with self.subTest(version=version_name):
                    adapter = create_adapter(version_name)
                    output = Path(directory) / f"{version_name}.zip"
                    DatapackBuilder.build(
                        output,
                        "particle_image",
                        "draw",
                        ["particle minecraft:flame ~ ~ ~ 0 0 0 0 1 normal"],
                        adapter,
                    )
                    with zipfile.ZipFile(output) as archive:
                        function_path = (
                            f"data/particle_image/{adapter.function_directory}/draw.mcfunction"
                        )
                        self.assertIn(function_path, archive.namelist())
                        self.assertNotIn(
                            "data/particle_image/functions/draw.mcfunction",
                            archive.namelist(),
                        )
                        metadata = json.loads(archive.read("pack.mcmeta"))["pack"]
                        self.assertEqual(metadata[format_key], format_value)

    def test_unknown_release_is_rejected_instead_of_guessing_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "暂不支持"):
            create_adapter("1.22")


if __name__ == "__main__":
    unittest.main()
