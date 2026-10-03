"""Editable particle model independent from Minecraft command strings."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from core.image_parser import ParsedImage
from core.rotation import Rotation3, Vector3
from core.transform import Transform


class PivotMode(str, Enum):
    LOWER_LEFT = "lower_left"
    CENTER = "center"
    CUSTOM = "custom"


@dataclass
class Particle:
    local_x: float
    local_y: float
    local_z: float
    color: tuple[int, int, int]
    alpha: float = 1.0
    size: float = 1.0
    rotation: Rotation3 = (0.0, 0.0, 0.0)
    visible: bool = True

    @property
    def local_position(self) -> Vector3:
        return self.local_x, self.local_y, self.local_z


@dataclass
class ParticleModel:
    particles: list[Particle] = field(default_factory=list)
    transform: Transform = field(default_factory=Transform)
    pivot_mode: PivotMode = PivotMode.LOWER_LEFT
    custom_pivot: Vector3 = (0.0, 0.0, 0.0)
    source_width: int = 0
    source_height: int = 0
    unit_spacing: float = 0.25
    particle_type: str = "dust"

    @property
    def pivot(self) -> Vector3:
        if self.pivot_mode == PivotMode.LOWER_LEFT:
            return 0.0, 0.0, 0.0
        if self.pivot_mode == PivotMode.CENTER:
            return (
                max(0, self.source_width - 1) / 2 * self.unit_spacing,
                max(0, self.source_height - 1) / 2 * self.unit_spacing,
                0.0,
            )
        return self.custom_pivot

    @classmethod
    def from_image(
        cls,
        image: ParsedImage,
        spacing: float = 0.25,
        particle_size: float = 1.0,
    ) -> ParticleModel:
        """Map the bottom-left image pixel to local origin (0, 0, 0)."""
        particles = [
            Particle(
                local_x=pixel.x * spacing,
                local_y=(image.height - 1 - pixel.y) * spacing,
                local_z=0.0,
                color=(pixel.red, pixel.green, pixel.blue),
                alpha=pixel.alpha / 255,
                size=particle_size,
            )
            for pixel in image.pixels
        ]
        return cls(
            particles=particles,
            source_width=image.width,
            source_height=image.height,
            unit_spacing=spacing,
        )

    def visible_particles(self) -> Iterable[Particle]:
        return (particle for particle in self.particles if particle.visible and particle.alpha > 0)
