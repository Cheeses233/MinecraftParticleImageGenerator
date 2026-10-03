"""Transform pipeline from model-local coordinates to executor-relative space."""

from __future__ import annotations

from dataclasses import dataclass

from core.rotation import Rotation3, Vector3, rotate_vector


@dataclass(frozen=True)
class Transform:
    position_offset: Vector3 = (0.0, 0.0, 0.0)
    rotation: Rotation3 = (0.0, 0.0, 0.0)
    scale: Vector3 = (1.0, 1.0, 1.0)

    def apply(self, local_position: Vector3, pivot: Vector3) -> Vector3:
        """Apply pivot-relative scale, rotation, then executor-relative offset."""
        relative: Vector3 = (
            local_position[0] - pivot[0],
            local_position[1] - pivot[1],
            local_position[2] - pivot[2],
        )
        scaled: Vector3 = (
            relative[0] * self.scale[0],
            relative[1] * self.scale[1],
            relative[2] * self.scale[2],
        )
        rotated = rotate_vector(scaled, self.rotation)
        return tuple(
            coordinate + offset
            for coordinate, offset in zip(rotated, self.position_offset)
        )
