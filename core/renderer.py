"""Convert editable local-space models to executor-relative MC functions."""

from __future__ import annotations

from core.coordinate_system import CoordinateSystem, OrientationMode
from core.particle_model import ParticleModel
from minecraft.mc1204_renderer import Minecraft1204Renderer
from minecraft.mc1205_renderer import Minecraft1205Renderer
from version.base import MinecraftVersionAdapter


class MinecraftRenderer:
    """Render a ParticleModel only at a function executor's context."""

    def __init__(self, adapter: MinecraftVersionAdapter) -> None:
        self.adapter = adapter
        if adapter.version_name == "1.20.4":
            self._particle_renderer = Minecraft1204Renderer()
        else:
            self._particle_renderer = Minecraft1205Renderer()

    def render(
        self,
        model: ParticleModel,
        orientation: OrientationMode = OrientationMode.EXECUTOR,
        force: bool = False,
    ) -> list[str]:
        """Emit commands using only relative (`~`) or local (`^`) positions."""
        visibility = "force" if force else "normal"
        commands: list[str] = []
        for particle in model.visible_particles():
            coordinate = CoordinateSystem.render(
                model,
                particle.local_position,
                orientation,
            )
            arguments = self._particle_renderer.particle_arguments(
                model.particle_type,
                particle,
            )
            x, y, z = coordinate.coordinate_tokens
            command = (
                f"particle {arguments} {x} {y} {z} "
                f"0 0 0 0 1 {visibility}"
            )
            commands.append(coordinate.command_prefix + command)
        return commands
