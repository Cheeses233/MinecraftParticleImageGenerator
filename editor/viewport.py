"""Interactive 3D-style particle viewport with orbit, pan, and grid controls."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QMouseEvent, QPaintEvent, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QWidget

from core.particle_model import ParticleModel
from editor.camera import OrbitCamera
from editor.gizmo import draw_axis_gizmo


class ParticleViewport(QWidget):
    """Paint an editable particle model using an interactive orbit camera."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(440, 360)
        self.setMouseTracking(True)
        self.camera = OrbitCamera()
        self.model: ParticleModel | None = None
        self.show_grid = True
        self.show_axes = True
        self._last_mouse_position = None

    def set_model(self, model: ParticleModel | None) -> None:
        self.model = model
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._last_mouse_position = event.position()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._last_mouse_position is None:
            return
        current = event.position()
        delta = current - self._last_mouse_position
        self._last_mouse_position = current
        buttons = event.buttons()
        if buttons & Qt.MouseButton.LeftButton:
            self.camera.orbit(delta.x(), delta.y())
        elif buttons & (Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton):
            self.camera.pan(delta.x(), delta.y())
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._last_mouse_position = None
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.camera.dolly(event.angleDelta().y() / 120)
        self.update()
        event.accept()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#171b22"))
        if self.show_grid:
            self._draw_grid(painter)
        self._draw_axes(painter)
        if self.model is not None:
            self._draw_particles(painter)
            self._draw_pivot(painter)
        if self.show_axes:
            draw_axis_gizmo(painter, self.camera, self.width(), self.height())
        painter.setPen(QColor("#bdc7d4"))
        painter.drawText(12, 22, "左键旋转 · 右键/中键平移 · 滚轮缩放")
        painter.end()

    def _project(self, point: tuple[float, float, float]) -> tuple[float, float, float]:
        if self.model is None:
            return self.camera.project(point, self.width(), self.height())
        transformed = self.model.transform.apply(point, self.model.pivot)
        return self.camera.project(transformed, self.width(), self.height())

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#2b323d"), 1))
        extent = 12
        for index in range(-extent, extent + 1):
            for start, end in (
                ((-extent, 0, index), (extent, 0, index)),
                ((index, 0, -extent), (index, 0, extent)),
            ):
                a = self.camera.project(start, self.width(), self.height())
                b = self.camera.project(end, self.width(), self.height())
                painter.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))

    def _draw_axes(self, painter: QPainter) -> None:
        origin = self.camera.project((0, 0, 0), self.width(), self.height())
        for point, color in (
            ((4, 0, 0), QColor("#ff6b6b")),
            ((0, 4, 0), QColor("#79d88f")),
            ((0, 0, 4), QColor("#65a9ff")),
        ):
            end = self.camera.project(point, self.width(), self.height())
            painter.setPen(QPen(color, 2))
            painter.drawLine(
                int(origin[0]),
                int(origin[1]),
                int(end[0]),
                int(end[1]),
            )

    def _draw_particles(self, painter: QPainter) -> None:
        assert self.model is not None
        visible = tuple(self.model.visible_particles())
        draw_limit = 40_000
        stride = max(1, (len(visible) + draw_limit - 1) // draw_limit)
        items = []
        for particle in visible[::stride]:
            transformed = self.model.transform.apply(
                particle.local_position,
                self.model.pivot,
            )
            position = self.camera.project(
                transformed,
                self.width(),
                self.height(),
            )
            items.append((position[2], position, particle))
        items.sort(key=lambda item: item[0], reverse=True)
        for _, (screen_x, screen_y, _), particle in items:
            radius = max(
                1.5,
                min(12.0, abs(particle.size) * self.camera.zoom * 0.12),
            )
            red, green, blue = particle.color
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor(
                    red,
                    green,
                    blue,
                    max(0, min(255, round(255 * particle.alpha))),
                )
            )
            painter.drawEllipse(
                int(screen_x - radius),
                int(screen_y - radius),
                int(radius * 2),
                int(radius * 2),
            )

    def _draw_pivot(self, painter: QPainter) -> None:
        if self.model is None:
            return
        pivot_position = self.model.transform.apply(
            self.model.pivot,
            self.model.pivot,
        )
        x, y, _ = self.camera.project(
            pivot_position,
            self.width(),
            self.height(),
        )
        painter.setPen(QPen(QColor("#fff2a8"), 2))
        painter.setBrush(QColor("#20242b"))
        painter.drawEllipse(int(x - 5), int(y - 5), 10, 10)
        painter.drawText(int(x + 8), int(y - 7), "Pivot")
