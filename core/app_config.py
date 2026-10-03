"""Persistent per-user settings stored as JSON under AppData."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from app_info import APP_NAME


@dataclass
class AppConfig:
    """The user-adjustable values restored by the desktop interface."""

    minecraft_version: str = "1.20.4"
    particle: str = "dust"
    scale: float = 1.0
    spacing: float = 0.25
    size: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0
    force: bool = False
    namespace: str = "particle_image"
    function_name: str = "draw"
    last_image: str = ""
    performance_mode: str = "medium"
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0
    model_scale_x: float = 1.0
    model_scale_y: float = 1.0
    model_scale_z: float = 1.0
    alpha: float = 1.0
    pivot_mode: str = "lower_left"
    pivot_x: float = 0.0
    pivot_y: float = 0.0
    pivot_z: float = 0.0
    orientation_mode: str = "executor"


def config_path() -> Path:
    """Return the current user's roaming AppData configuration file path."""
    app_data = os.environ.get("APPDATA")
    if not app_data:
        raise OSError("无法定位 Windows AppData 目录，不能保存用户设置。")
    return Path(app_data) / APP_NAME / "config.json"


def load_config() -> AppConfig:
    """Load settings, using defaults only when the file does not exist."""
    path = config_path()
    if not path.exists():
        return AppConfig()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("配置文件根节点必须是 JSON 对象。")
        config = AppConfig(**raw)
        for name in (
            "scale",
            "spacing",
            "size",
            "offset_x",
            "offset_y",
            "offset_z",
            "rotation_x",
            "rotation_y",
            "rotation_z",
            "model_scale_x",
            "model_scale_y",
            "model_scale_z",
            "alpha",
            "pivot_x",
            "pivot_y",
            "pivot_z",
        ):
            value = getattr(config, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"配置项 {name} 必须为有限数字。")
        if not isinstance(config.force, bool):
            raise ValueError("配置项 force 必须为布尔值。")
        if not all(
            isinstance(value, str)
            for value in (
                config.minecraft_version,
                config.particle,
                config.namespace,
                config.function_name,
                config.last_image,
                config.performance_mode,
                config.pivot_mode,
                config.orientation_mode,
            )
        ):
            raise ValueError("配置中的文本项目必须是字符串。")
        return config
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError(f"用户配置文件无法读取：{path}\n{error}") from error


def save_config(config: AppConfig) -> Path:
    """Atomically persist settings and return the destination path."""
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path
