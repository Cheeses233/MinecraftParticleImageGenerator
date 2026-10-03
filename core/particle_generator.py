"""Convert parsed image pixels into version-adapted particle commands."""

from __future__ import annotations

import math

from core.coordinate_system import OrientationMode
from core.image_parser import ParsedImage
from core.particle_model import ParticleModel
from core.renderer import MinecraftRenderer
from core.transform import Transform
from version.base import MinecraftVersionAdapter


SUPPORTED_PARTICLES = ("dust", "flame", "cloud", "end_rod")


class ParticleGenerator:
    """Lay out image pixels in 3D space and render their commands."""

    @staticmethod
    def generate(
        image: ParsedImage,
        adapter: MinecraftVersionAdapter,
        particle: str,
        spacing: float,
        offset: tuple[float, float, float],
        size: float,
        force: bool,
        orientation: OrientationMode = OrientationMode.EXECUTOR,
    ) -> list[str]:
        if particle not in SUPPORTED_PARTICLES:
            raise ValueError(f"不支持的粒子类型：{particle}")
        if not math.isfinite(spacing) or spacing <= 0:
            raise ValueError("粒子间距必须是大于 0 的有限数值。")
        if not math.isfinite(size) or size <= 0:
            raise ValueError("粒子大小必须是大于 0 的有限数值。")
        if len(offset) != 3 or not all(math.isfinite(value) for value in offset):
            raise ValueError("XYZ 偏移必须是有限数值。")

        model = ParticleModel.from_image(
            image,
            spacing=spacing,
            particle_size=size,
        )
        model.particle_type = particle
        model.transform = Transform(position_offset=offset)
        return MinecraftRenderer(adapter).render(model, orientation, force)
