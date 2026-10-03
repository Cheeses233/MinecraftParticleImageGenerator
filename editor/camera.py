"""Orbit camera and projection for the particle model viewport."""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.rotation import Vector3


@dataclass
class OrbitCamera:
    yaw_degrees: float = -35.0
    pitch_degrees: float = 25.0
    zoom: float = 32.0
    pan_x: float = 0.0
    pan_y: float = 0.0

    def project(
        self,
        point: Vector3,
        width: int,
        height: int,
    ) -> tuple[float, float, float]:
        yaw = math.radians(self.yaw_degrees)
        pitch = math.radians(self.pitch_degrees)
        x, y, z = point
        turned_x = math.cos(yaw) * x - math.sin(yaw) * z
        turned_z = math.sin(yaw) * x + math.cos(yaw) * z
        turned_y = math.cos(pitch) * y - math.sin(pitch) * turned_z
        depth = math.sin(pitch) * y + math.cos(pitch) * turned_z
        return (
            width / 2 + self.pan_x + turned_x * self.zoom,
            height / 2 + self.pan_y - turned_y * self.zoom,
            depth,
        )

    def orbit(self, delta_x: float, delta_y: float) -> None:
        self.yaw_degrees += delta_x * 0.6
        self.pitch_degrees = max(
            -89.0,
            min(89.0, self.pitch_degrees + delta_y * 0.6),
        )

    def pan(self, delta_x: float, delta_y: float) -> None:
        self.pan_x += delta_x
        self.pan_y += delta_y

    def dolly(self, wheel_steps: float) -> None:
        self.zoom = max(2.0, min(500.0, self.zoom * (1.12**wheel_steps)))
