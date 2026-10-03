"""Minecraft Java Edition 1.20.4 particle command syntax."""

from __future__ import annotations

from core.particle_model import Particle


class Minecraft1204Renderer:
    """Render particle arguments using the pre-1.20.5 command format."""

    @staticmethod
    def particle_arguments(particle_type: str, particle: Particle) -> str:
        if particle_type == "dust":
            red, green, blue = (component / 255 for component in particle.color)
            return (
                "dust "
                f"{red:.4f} {green:.4f} {blue:.4f} {particle.size:.4f}"
            )
        if particle_type in {"flame", "cloud", "end_rod"}:
            return f"minecraft:{particle_type}"
        raise ValueError(f"Unsupported Minecraft particle type: {particle_type}")
