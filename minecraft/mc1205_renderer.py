"""Minecraft Java Edition 1.20.5+ particle command syntax."""

from __future__ import annotations

from core.particle_model import Particle


class Minecraft1205Renderer:
    """Render particle arguments using the component-style particle syntax."""

    @staticmethod
    def particle_arguments(particle_type: str, particle: Particle) -> str:
        if particle_type == "dust":
            red, green, blue = (component / 255 for component in particle.color)
            return (
                "minecraft:dust{color:["
                f"{red:.4f}f,{green:.4f}f,{blue:.4f}f],"
                f"scale:{particle.size:.4f}f}}"
            )
        if particle_type in {"flame", "cloud", "end_rod"}:
            return f"minecraft:{particle_type}"
        raise ValueError(f"Unsupported Minecraft particle type: {particle_type}")
