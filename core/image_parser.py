"""PNG, GIF, and APNG loading with scaling and transparent-pixel filtering."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.performance import (
    LIMITS,
    MAX_ANIMATION_FRAMES,
    MAX_ANIMATION_TOTAL_PIXELS,
    PerformanceMode,
)


@dataclass(frozen=True)
class Pixel:
    """An opaque image pixel in image-local coordinates."""

    x: int
    y: int
    red: int
    green: int
    blue: int
    alpha: int


@dataclass(frozen=True)
class ParsedImage:
    """A scaled image represented by its non-transparent pixels."""

    width: int
    height: int
    pixels: tuple[Pixel, ...]


@dataclass(frozen=True)
class ParsedAnimation:
    """A bounded animation ready for preview and datapack export."""

    frames: tuple[ParsedImage, ...]
    durations_ms: tuple[int, ...]

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def total_particles(self) -> int:
        return sum(len(frame.pixels) for frame in self.frames)


class ImageParser:
    """Convert supported raster images into pixels for particle generation."""

    @staticmethod
    def parse(
        path: str | Path,
        scale: float = 1.0,
        mode: PerformanceMode = PerformanceMode.MEDIUM,
    ) -> ParsedImage:
        """Load the first frame of an image using the selected quality mode."""
        animation = ImageParser.parse_animation(path, scale, mode)
        first_frame = animation.frames[0]
        if not first_frame.pixels:
            raise ValueError("图片第一帧中没有可见像素。")
        return first_frame

    @staticmethod
    def parse_animation(
        path: str | Path,
        scale: float = 1.0,
        mode: PerformanceMode = PerformanceMode.MEDIUM,
    ) -> ParsedAnimation:
        """Load a still image or all GIF/APNG frames within safe size limits."""
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("缩放比例必须大于 0。")

        image_path = Path(path)
        try:
            with Image.open(image_path) as source:
                if source.format not in {"PNG", "GIF"}:
                    raise ValueError("请选择 PNG、GIF 或 APNG 图片。")
                frame_count = getattr(source, "n_frames", 1)
                if frame_count > MAX_ANIMATION_FRAMES:
                    raise ValueError(
                        f"动画包含 {frame_count} 帧，最多支持 "
                        f"{MAX_ANIMATION_FRAMES} 帧。"
                    )
                limits = LIMITS[mode]
                per_frame_budget = min(
                    limits.max_pixels,
                    max(1, MAX_ANIMATION_TOTAL_PIXELS // frame_count),
                )
                frames: list[ParsedImage] = []
                durations: list[int] = []
                for frame_index in range(frame_count):
                    source.seek(frame_index)
                    frame = source.convert("RGBA")
                    frame = ImageParser._resize(
                        frame,
                        scale,
                        per_frame_budget,
                        limits.max_edge,
                        limits.resample_low,
                    )
                    frames.append(ImageParser._to_pixels(frame, allow_empty=True))
                    duration = source.info.get("duration", 100)
                    durations.append(
                        max(20, int(duration)) if isinstance(duration, (int, float)) else 100
                    )
        except (OSError, UnidentifiedImageError) as error:
            raise ValueError(f"无法读取图片：{error}") from error

        if not any(frame.pixels for frame in frames):
            raise ValueError("图片中没有可见像素。")
        return ParsedAnimation(tuple(frames), tuple(durations))

    @staticmethod
    def _resize(
        image: Image.Image,
        scale: float,
        max_pixels: int,
        max_edge: int | None,
        low_quality: bool,
    ) -> Image.Image:
        width = max(1, round(image.width * scale))
        height = max(1, round(image.height * scale))
        reduction = min(1.0, math.sqrt(max_pixels / (width * height)))
        if max_edge is not None:
            reduction = min(reduction, max_edge / max(width, height))
        target_size = (
            max(1, round(width * reduction)),
            max(1, round(height * reduction)),
        )
        if target_size == image.size:
            return image
        resampling = Image.Resampling.BOX if low_quality else Image.Resampling.LANCZOS
        return image.resize(target_size, resampling)

    @staticmethod
    def _to_pixels(image: Image.Image, allow_empty: bool = False) -> ParsedImage:
        pixels: list[Pixel] = []
        for y in range(image.height):
            for x in range(image.width):
                red, green, blue, alpha = image.getpixel((x, y))
                if alpha > 0:
                    pixels.append(Pixel(x, y, red, green, blue, alpha))
        if not pixels and not allow_empty:
            raise ValueError("图片中没有可见像素。")
        return ParsedImage(image.width, image.height, tuple(pixels))
