"""Tests for animation parsing, prediction, and looping datapack output."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image

from core.datapack_builder import DatapackBuilder
from core.image_parser import ImageParser
from core.performance import PerformanceMode
from core.prediction import predict_generation
from version.registry import create_adapter


class AnimationPipelineTests(unittest.TestCase):
    def test_gif_frames_and_durations_are_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "animation.gif"
            frames = [
                Image.new("RGBA", (4, 4), (255, 0, 0, 255)),
                Image.new("RGBA", (4, 4), (0, 0, 255, 255)),
            ]
            frames[0].save(
                path,
                save_all=True,
                append_images=frames[1:],
                duration=[100, 250],
                loop=0,
                disposal=2,
            )

            animation = ImageParser.parse_animation(path)
            self.assertEqual(animation.frame_count, 2)
            self.assertEqual(animation.durations_ms, (100, 250))
            self.assertEqual(animation.frames[0].pixels[0].red, 255)
            self.assertEqual(animation.frames[1].pixels[0].blue, 255)

    def test_performance_modes_reduce_resolution_as_promised(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.png"
            Image.new("RGBA", (512, 512), (100, 120, 140, 255)).save(path)

            low = ImageParser.parse(path, mode=PerformanceMode.LOW)
            medium = ImageParser.parse(path, mode=PerformanceMode.MEDIUM)
            high = ImageParser.parse(path, mode=PerformanceMode.HIGH)
            self.assertLessEqual(max(low.width, low.height), 128)
            self.assertEqual((medium.width, medium.height), (512, 512))
            self.assertEqual((high.width, high.height), (512, 512))
            self.assertEqual(len(low.pixels), low.width * low.height)

    def test_apng_frames_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "animation.png"
            frames = [
                Image.new("RGBA", (3, 2), (255, 0, 0, 255)),
                Image.new("RGBA", (3, 2), (0, 255, 0, 255)),
            ]
            frames[0].save(
                path,
                save_all=True,
                append_images=frames[1:],
                duration=[100, 200],
                loop=0,
                format="PNG",
            )
            animation = ImageParser.parse_animation(path)
            self.assertEqual(animation.frame_count, 2)
            self.assertEqual(animation.frames[1].pixels[0].green, 255)

    def test_prediction_reports_counts_size_and_high_command_risk(self) -> None:
        from core.image_parser import ParsedAnimation, ParsedImage

        frame = ParsedImage(1, 1, ())
        animation = ParsedAnimation((frame,), (100,))
        commands = tuple(f"particle test:{index}" for index in range(65_536))
        prediction = predict_generation(animation, (commands,))
        self.assertEqual(prediction.particle_count, 65_536)
        self.assertGreater(prediction.mcfunction_bytes, 0)
        self.assertEqual(prediction.risk_level, "high")

    def test_animation_datapack_loops_frames_and_has_start_stop_functions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "loop.zip"
            DatapackBuilder.build_animation(
                output,
                "particle_image",
                "draw",
                (
                    ("particle minecraft:flame ~ ~ ~ 0 0 0 0 1 normal",),
                    ("particle minecraft:cloud ~ ~ ~ 0 0 0 0 1 normal",),
                ),
                (2, 5),
                create_adapter("1.21.9"),
            )
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                prefix = "data/particle_image/function/draw/animation"
                self.assertIn(f"{prefix}/start.mcfunction", names)
                self.assertIn(f"{prefix}/stop.mcfunction", names)
                first = archive.read(f"{prefix}/frame_000.mcfunction").decode()
                second = archive.read(f"{prefix}/frame_001.mcfunction").decode()
                start = archive.read(f"{prefix}/start.mcfunction").decode()
                stop = archive.read(f"{prefix}/stop.mcfunction").decode()
                metadata = json.loads(archive.read("pack.mcmeta"))["pack"]
                self.assertIn("particle_image:draw/animation/frame_001 2t", first)
                self.assertIn("particle_image:draw/animation/frame_000 5t", second)
                self.assertIn("schedule clear particle_image:draw/animation/frame_000", stop)
                self.assertIn("tag @s add particle_image_particle_image_draw_runner", start)
                self.assertIn(
                    "execute as @e[tag=particle_image_particle_image_draw_runner] at @s run",
                    first,
                )
                self.assertIn(
                    "tag @e[tag=particle_image_particle_image_draw_runner] remove",
                    stop,
                )
                self.assertIn("min_format", metadata)


if __name__ == "__main__":
    unittest.main()
