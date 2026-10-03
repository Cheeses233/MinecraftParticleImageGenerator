"""Resolution and processing budgets for image generation modes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PerformanceMode(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class PerformanceLimits:
    """Limits applied after the user's requested image scaling."""

    max_pixels: int
    max_edge: int | None
    resample_low: bool


LIMITS: dict[PerformanceMode, PerformanceLimits] = {
    PerformanceMode.LOW: PerformanceLimits(
        max_pixels=16_384,
        max_edge=128,
        resample_low=True,
    ),
    PerformanceMode.MEDIUM: PerformanceLimits(
        max_pixels=500_000,
        max_edge=None,
        resample_low=False,
    ),
    PerformanceMode.HIGH: PerformanceLimits(
        max_pixels=1_000_000,
        max_edge=None,
        resample_low=False,
    ),
}

MAX_ANIMATION_FRAMES = 120
MAX_ANIMATION_TOTAL_PIXELS = 2_000_000


def performance_label(mode: PerformanceMode) -> str:
    return {
        PerformanceMode.LOW: "低 — 降低分辨率并合并像素",
        PerformanceMode.MEDIUM: "中 — 保持质量",
        PerformanceMode.HIGH: "高 — 最大精度（最多 100 万像素）",
    }[mode]
