"""Pre-export estimates for command count, file size, and runtime risk."""

from __future__ import annotations

from dataclasses import dataclass

from core.image_parser import ParsedAnimation


@dataclass(frozen=True)
class GenerationPrediction:
    particle_count: int
    mcfunction_bytes: int
    largest_frame_particles: int
    risk_level: str
    risk_message: str


def predict_generation(
    animation: ParsedAnimation,
    commands_per_frame: tuple[tuple[str, ...], ...],
) -> GenerationPrediction:
    """Estimate uncompressed function bytes and per-tick command pressure."""
    if len(commands_per_frame) != animation.frame_count:
        raise ValueError("预测命令帧数与图片帧数不匹配。")

    particle_count = sum(len(frame) for frame in commands_per_frame)
    largest_frame = max((len(frame) for frame in commands_per_frame), default=0)
    function_bytes = sum(
        len(command.encode("utf-8")) + 1
        for frame in commands_per_frame
        for command in frame
    )
    if animation.frame_count > 1:
        # Include per-frame scheduler lines, the animation start, and stop cleanup.
        function_bytes += animation.frame_count * 160 + 80

    if largest_frame >= 65_536:
        level = "high"
        message = (
            "单帧命令达到 Minecraft 默认每刻命令序列上限 65,536，"
            "超出部分可能不执行。"
        )
    elif largest_frame >= 20_000 or function_bytes >= 5_000_000:
        level = "high"
        message = "单帧命令量或函数文本较大，可能造成明显卡顿或触及服务器限制。"
    elif largest_frame >= 5_000 or function_bytes >= 1_000_000:
        level = "medium"
        message = "命令量偏高，执行期间可能出现短暂卡顿。"
    else:
        level = "low"
        message = "预计风险较低；动画每次仅执行当前帧的粒子命令。"

    return GenerationPrediction(
        particle_count=particle_count,
        mcfunction_bytes=function_bytes,
        largest_frame_particles=largest_frame,
        risk_level=level,
        risk_message=message,
    )
