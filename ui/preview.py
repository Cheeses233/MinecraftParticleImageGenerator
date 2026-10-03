"""Image preview and lightweight Minecraft-style particle simulation widgets."""

from __future__ import annotations

import time
import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPaintEvent, QPainter, QPixmap, QResizeEvent
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget

from core.image_parser import ParsedAnimation, ParsedImage


def parsed_image_pixmap(image: ParsedImage) -> QPixmap:
    """Convert RGBA pixels to a Qt image without per-pixel painter calls."""
    buffer = bytearray(image.width * image.height * 4)
    for pixel in image.pixels:
        offset = (pixel.y * image.width + pixel.x) * 4
        buffer[offset : offset + 4] = bytes(
            (pixel.red, pixel.green, pixel.blue, pixel.alpha)
        )
    qimage = QImage(
        buffer,
        image.width,
        image.height,
        image.width * 4,
        QImage.Format.Format_RGBA8888,
    )
    return QPixmap.fromImage(qimage.copy())


class ImagePreviewDialog(QDialog):
    """A separate fit-to-window preview for imported stills and animations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("图片预览")
        self.resize(850, 700)
        self._pixmaps: tuple[QPixmap, ...] = ()
        self._durations: tuple[int, ...] = ()
        self._frame_index = 0
        self._label = QLabel("尚未导入图片")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("background: #20242b; color: #d7dce2;")
        self._status = QLabel("")
        layout = QVBoxLayout(self)
        layout.addWidget(self._label, stretch=1)
        layout.addWidget(self._status)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)

    def set_animation(self, path: str, animation: ParsedAnimation) -> None:
        self._pixmaps = tuple(
            parsed_image_pixmap(frame) for frame in animation.frames
        )
        self._durations = animation.durations_ms
        self._frame_index = 0
        self.setWindowTitle(f"图片预览 — {path}")
        self._show_frame()
        self._timer.stop()
        if len(self._pixmaps) > 1:
            self._timer.start(self._durations[0])

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._show_frame()

    def _advance_frame(self) -> None:
        if not self._pixmaps:
            return
        self._frame_index = (self._frame_index + 1) % len(self._pixmaps)
        self._show_frame()
        self._timer.start(self._durations[self._frame_index])

    def _show_frame(self) -> None:
        if not self._pixmaps:
            return
        self._label.setPixmap(
            self._pixmaps[self._frame_index].scaled(
                self._label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self._status.setText(
            f"帧 {self._frame_index + 1}/{len(self._pixmaps)}"
        )


class ParticleSimulationWidget(QWidget):
    """Render the selected image as animated, particle-shaped preview marks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(340, 300)
        self._animation: ParsedAnimation | None = None
        self._particle = "dust"
        self._spacing = 1.0
        self._size = 1.0
        self._offset = (0.0, 0.0, 0.0)
        self._frame_index = 0
        self._started_at = time.monotonic()
        self._preview_pixmap: QPixmap | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)

    def set_animation(
        self,
        animation: ParsedAnimation | None,
        particle: str,
        spacing: float = 1.0,
        size: float = 1.0,
        offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        self._animation = animation
        self._particle = particle
        self._spacing = spacing
        self._size = size
        self._offset = offset
        self._started_at = time.monotonic()
        self._frame_index = 0
        self._preview_pixmap = None
        if animation is not None:
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tick(self) -> None:
        if self._animation is not None and self._animation.frame_count > 1:
            elapsed_ms = (time.monotonic() - self._started_at) * 1000
            total_duration = sum(self._animation.durations_ms)
            current = elapsed_ms % total_duration
            accumulated = 0
            for index, duration in enumerate(self._animation.durations_ms):
                accumulated += duration
                if current < accumulated:
                    self._frame_index = index
                    break
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#171b22"))
        if self._animation is None:
            painter.setPen(QColor("#d7dce2"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "粒子模拟预览")
            return

        frame = self._animation.frames[self._frame_index]
        if not frame.pixels:
            painter.setPen(QColor("#d7dce2"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "当前帧透明")
            return

        margin = 18
        cell = min(
            (self.width() - margin * 2) / max(1.0, frame.width * self._spacing),
            (self.height() - margin * 2) / max(1.0, frame.height * self._spacing),
        )
        image_width = frame.width * self._spacing * cell
        image_height = frame.height * self._spacing * cell
        left = (self.width() - image_width) / 2
        top = (self.height() - image_height) / 2

        particle_limit = 20_000
        stride = max(1, (len(frame.pixels) + particle_limit - 1) // particle_limit)
        phase = time.monotonic() * 7
        for index in range(0, len(frame.pixels), stride):
            pixel = frame.pixels[index]
            x = left + (pixel.x + 0.5) * self._spacing * cell
            y = top + (pixel.y + 0.5) * self._spacing * cell
            if self._particle == "dust":
                color = QColor(pixel.red, pixel.green, pixel.blue, pixel.alpha)
                radius = max(1.0, min(cell * 0.43 * self._size, 5.0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(
                    int(x - radius),
                    int(y - radius),
                    int(radius * 2),
                    int(radius * 2),
                )
            elif self._particle == "flame":
                flicker = 0.8 + 0.2 * abs(math.sin(phase + index))
                color = QColor(255, int(105 + 95 * flicker), 35, 235)
                radius = max(1.0, min(cell * 0.42, 5.0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(
                    int(x - radius),
                    int(y - radius - flicker),
                    int(radius * 2),
                    int(radius * 2),
                )
            elif self._particle == "cloud":
                color = QColor(205, 213, 222, 155)
                radius = max(1.0, min(cell * 0.48, 6.0))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(
                    int(x - radius),
                    int(y - radius),
                    int(radius * 2),
                    int(radius * 2),
                )
            else:
                color = QColor(235, 249, 255, 235)
                radius = max(1.0, min(cell * 0.28, 4.0))
                painter.setPen(color)
                painter.drawLine(int(x - radius), int(y), int(x + radius), int(y))
                painter.drawLine(int(x), int(y - radius), int(x), int(y + radius))

        painter.setPen(QColor("#aeb8c5"))
        painter.drawText(
            10,
            self.height() - 8,
            f"模拟显示 {min(len(frame.pixels), particle_limit):,}/"
            f"{len(frame.pixels):,} 粒子 · 帧 {self._frame_index + 1}/"
            f"{self._animation.frame_count} · 坐标偏移 "
            f"{self._offset[0]:g}, {self._offset[1]:g}, {self._offset[2]:g}",
        )
        painter.end()
