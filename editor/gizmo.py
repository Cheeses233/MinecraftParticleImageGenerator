"""Screen-space XYZ axis gizmo for the model viewport."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPainter, QPen

from editor.camera import OrbitCamera


def draw_axis_gizmo(painter: QPainter, camera: OrbitCamera, width: int, height: int) -> None:
    origin = (52.0, height - 48.0)
    axes = (
        ((1.0, 0.0, 0.0), QColor("#ff6b6b"), "X"),
        ((0.0, 1.0, 0.0), QColor("#79d88f"), "Y"),
        ((0.0, 0.0, 1.0), QColor("#65a9ff"), "Z"),
    )
    for axis, color, label in axes:
        projected = camera.project(axis, width, height)
        delta_x = (projected[0] - width / 2) / camera.zoom * 36
        delta_y = (projected[1] - height / 2) / camera.zoom * 36
        painter.setPen(QPen(color, 2))
        painter.drawLine(
            int(origin[0]),
            int(origin[1]),
            int(origin[0] + delta_x),
            int(origin[1] + delta_y),
        )
        painter.drawText(
            int(origin[0] + delta_x + 4),
            int(origin[1] + delta_y),
            label,
        )
