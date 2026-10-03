"""Create a Minecraft datapack ZIP from generated commands."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Sequence

from version.base import MinecraftVersionAdapter


class DatapackBuilder:
    """Package a function and metadata into a datapack archive."""

    _NAMESPACE_PATTERN = re.compile(r"^[a-z0-9_.-]+$")
    _FUNCTION_PATTERN = re.compile(r"^[a-z0-9_./-]+$")

    @classmethod
    def build(
        cls,
        output_path: str | Path,
        namespace: str,
        function_name: str,
        commands: Sequence[str],
        adapter: MinecraftVersionAdapter,
    ) -> Path:
        """Write a datapack ZIP and return its absolute path."""
        if not cls._NAMESPACE_PATTERN.fullmatch(namespace):
            raise ValueError("命名空间只能包含小写字母、数字、下划线、连字符和点。")
        if (
            not cls._FUNCTION_PATTERN.fullmatch(function_name)
            or any(part in {"", ".", ".."} for part in function_name.split("/"))
        ):
            raise ValueError("函数名称包含无效字符或路径。")
        if not commands:
            raise ValueError("没有可写入函数包的粒子命令。")

        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        metadata = adapter.pack_metadata()
        function_path = (
            f"data/{namespace}/{adapter.function_directory}/"
            f"{function_name}.mcfunction"
        )
        function_content = "\n".join(commands) + "\n"

        with zipfile.ZipFile(
            target, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr(
                "pack.mcmeta",
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            )
            archive.writestr(function_path, function_content)
        return target

    @classmethod
    def build_animation(
        cls,
        output_path: str | Path,
        namespace: str,
        function_name: str,
        frames: Sequence[Sequence[str]],
        durations_ticks: Sequence[int],
        adapter: MinecraftVersionAdapter,
        executor_tag: str | None = None,
    ) -> Path:
        """Package an executor-bound loop plus user-callable start/stop files."""
        cls._validate_identifier(namespace, function_name)
        if not frames or len(frames) != len(durations_ticks):
            raise ValueError("动画至少需要一帧，且每帧必须有对应的播放时长。")
        if any(duration < 1 for duration in durations_ticks):
            raise ValueError("动画帧时长必须至少为 1 tick。")

        target = Path(output_path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        root = f"data/{namespace}/{adapter.function_directory}"
        animation_path = f"{function_name}/animation"
        if executor_tag is None:
            executor_tag = cls.animation_tag(namespace, function_name)
        if not re.fullmatch(r"[a-z0-9_.-]+", executor_tag):
            raise ValueError("动画执行者标签包含无效字符。")
        frame_ids = [
            f"{function_name}/animation/frame_{index:03d}"
            for index in range(len(frames))
        ]
        with zipfile.ZipFile(
            target, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr(
                "pack.mcmeta",
                json.dumps(adapter.pack_metadata(), ensure_ascii=False, indent=2)
                + "\n",
            )
            start_path = f"{root}/{animation_path}/start.mcfunction"
            archive.writestr(
                start_path,
                f"tag @s add {executor_tag}\n"
                f"schedule function {namespace}:{frame_ids[0]} 1t replace\n",
            )
            stop_path = f"{root}/{animation_path}/stop.mcfunction"
            archive.writestr(
                stop_path,
                "".join(
                    f"schedule clear {namespace}:{frame_id}\n"
                    for frame_id in frame_ids
                )
                + f"tag @e[tag={executor_tag}] remove {executor_tag}\n",
            )

            for index, commands in enumerate(frames):
                next_index = (index + 1) % len(frames)
                content = "".join(
                    f"execute as @e[tag={executor_tag}] at @s run {command}\n"
                    for command in commands
                )
                content += (
                    f"schedule function {namespace}:{frame_ids[next_index]} "
                    f"{durations_ticks[index]}t replace\n"
                )
                archive.writestr(
                    f"{root}/{frame_ids[index]}.mcfunction",
                    content,
                )
        return target

    @staticmethod
    def animation_tag(namespace: str, function_name: str) -> str:
        safe_name = re.sub(r"[^a-z0-9_.-]", "_", f"{namespace}_{function_name}")
        return f"particle_image_{safe_name}_runner"

    @classmethod
    def _validate_identifier(cls, namespace: str, function_name: str) -> None:
        if not cls._NAMESPACE_PATTERN.fullmatch(namespace):
            raise ValueError("命名空间只能包含小写字母、数字、下划线、连字符和点。")
        if (
            not cls._FUNCTION_PATTERN.fullmatch(function_name)
            or any(part in {"", ".", ".."} for part in function_name.split("/"))
        ):
            raise ValueError("函数名称包含无效字符或路径。")
