"""Tests for local-space particle models and executor-relative rendering."""

from __future__ import annotations

import unittest

from core.coordinate_system import CoordinateSystem, OrientationMode
from core.image_parser import ParsedImage, Pixel
from core.particle_model import ParticleModel, PivotMode
from core.renderer import MinecraftRenderer
from core.transform import Transform
from version.registry import create_adapter


class ParticleModelRenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = ParsedImage(
            width=2,
            height=2,
            pixels=(
                Pixel(0, 0, 255, 0, 0, 255),
                Pixel(1, 1, 0, 255, 0, 128),
            ),
        )

    def test_image_coordinates_are_local_with_lower_left_as_origin(self) -> None:
        model = ParticleModel.from_image(self.image, spacing=0.5)
        self.assertEqual(model.particles[0].local_position, (0.0, 0.5, 0.0))
        self.assertEqual(model.particles[1].local_position, (0.5, 0.0, 0.0))
        self.assertEqual(model.pivot, (0.0, 0.0, 0.0))

    def test_transform_scales_then_rotates_then_adds_executor_offset(self) -> None:
        model = ParticleModel.from_image(self.image, spacing=1.0)
        model.transform = Transform(
            position_offset=(10.0, 20.0, 30.0),
            rotation=(0.0, 0.0, 90.0),
            scale=(2.0, 1.0, 1.0),
        )
        transformed = model.transform.apply((1.0, 0.0, 0.0), model.pivot)
        self.assertAlmostEqual(transformed[0], 10.0)
        self.assertAlmostEqual(transformed[1], 22.0)
        self.assertAlmostEqual(transformed[2], 30.0)

    def test_center_and_custom_pivots_are_in_model_local_units(self) -> None:
        model = ParticleModel.from_image(self.image, spacing=0.5)
        model.pivot_mode = PivotMode.CENTER
        self.assertEqual(model.pivot, (0.25, 0.25, 0.0))
        model.pivot_mode = PivotMode.CUSTOM
        model.custom_pivot = (0.1, 0.2, 0.3)
        self.assertEqual(model.pivot, (0.1, 0.2, 0.3))

    def test_executor_and_player_modes_emit_local_not_absolute_coordinates(self) -> None:
        model = ParticleModel.from_image(self.image, spacing=0.5)
        model.transform = Transform(position_offset=(2.0, 3.0, 4.0))

        executor_commands = MinecraftRenderer(create_adapter("1.21.8")).render(
            model,
            OrientationMode.EXECUTOR,
        )
        self.assertIn("particle minecraft:dust", executor_commands[0])
        self.assertIn(" ^-2 ^3.5 ^4 ", executor_commands[0])
        self.assertNotIn("execute positioned", executor_commands[0])
        relative_tokens = executor_commands[0].split()[2:5]
        self.assertTrue(all(token.startswith("^") for token in relative_tokens))

        player_coordinate = CoordinateSystem.render(
            model,
            model.particles[0].local_position,
            OrientationMode.PLAYER_VIEW,
        )
        self.assertEqual(player_coordinate.command_prefix, "execute rotated as @p run ")

    def test_fixed_world_mode_still_uses_relative_executor_position(self) -> None:
        model = ParticleModel.from_image(self.image)
        command = MinecraftRenderer(create_adapter("1.21.8")).render(
            model,
            OrientationMode.WORLD_FIXED,
        )[0]
        self.assertIn("execute rotated 0 0 run particle", command)
        self.assertIn(" ~0 ~0.25 ~0 ", command)
        relative_tokens = command.split("run ", maxsplit=1)[1].split()[2:5]
        self.assertTrue(all(token.startswith("~") for token in relative_tokens))

    def test_renderer_selects_version_correct_dust_syntax(self) -> None:
        model = ParticleModel.from_image(self.image)
        command_1204 = MinecraftRenderer(create_adapter("1.20.4")).render(
            model,
            OrientationMode.EXECUTOR,
        )[0]
        command_1205 = MinecraftRenderer(create_adapter("1.20.5")).render(
            model,
            OrientationMode.EXECUTOR,
        )[0]
        self.assertIn("particle dust 1.0000 0.0000 0.0000", command_1204)
        self.assertIn("particle minecraft:dust{color:", command_1205)


if __name__ == "__main__":
    unittest.main()
