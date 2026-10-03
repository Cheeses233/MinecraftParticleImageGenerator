"""Minecraft executor position and orientation coordinate conversion."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.particle_model import ParticleModel
from core.rotation import Vector3


class OrientationMode(str, Enum):
    WORLD_FIXED = "world_fixed"
    EXECUTOR = "executor"
    PLAYER_VIEW = "player_view"


@dataclass(frozen=True)
class RenderedCoordinate:
    position: Vector3
    coordinate_tokens: tuple[str, str, str]
    command_prefix: str


class CoordinateSystem:
    """Convert transformed local positions into executor-relative MC tokens."""

    @staticmethod
    def format_number(value: float) -> str:
        rounded = round(value, 4)
        if rounded == 0:
            rounded = 0
        return f"{rounded:.4f}".rstrip("0").rstrip(".") or "0"

    @classmethod
    def render(
        cls,
        model: ParticleModel,
        local_position: Vector3,
        mode: OrientationMode,
    ) -> RenderedCoordinate:
        transformed = model.transform.apply(local_position, model.pivot)
        x, y, z = transformed
        if mode == OrientationMode.WORLD_FIXED:
            tokens = tuple(f"~{cls.format_number(value)}" for value in transformed)
            prefix = "execute rotated 0 0 run "
        else:
            # Minecraft local X is positive to the executor's left; image +X is right.
            tokens = (
                f"^{cls.format_number(-x)}",
                f"^{cls.format_number(y)}",
                f"^{cls.format_number(z)}",
            )
            prefix = (
                "execute rotated as @p run "
                if mode == OrientationMode.PLAYER_VIEW
                else ""
            )
        return RenderedCoordinate(transformed, tokens, prefix)
