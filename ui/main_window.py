"""Main PySide6 window for generating particle image datapacks."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QPixmap, QResizeEvent
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app_info import APP_VERSION
from core.app_config import AppConfig, load_config, save_config
from core.coordinate_system import OrientationMode
from core.datapack_builder import DatapackBuilder
from core.image_parser import ImageParser, ParsedAnimation
from core.particle_model import ParticleModel, PivotMode
from core.performance import PerformanceMode, performance_label
from core.particle_generator import SUPPORTED_PARTICLES
from core.prediction import GenerationPrediction, predict_generation
from core.renderer import MinecraftRenderer
from core.transform import Transform
from editor.viewport import ParticleViewport
from ui.preview import ImagePreviewDialog, ParticleSimulationWidget, parsed_image_pixmap
from version.base import MinecraftVersionAdapter
from version.registry import SUPPORTED_VERSIONS, create_adapter

logger = logging.getLogger(__name__)


class _PredictionSignals(QObject):
    completed = Signal(int, object, object)


class _PredictionWorker(QRunnable):
    """Build cached commands and predictions away from the GUI thread."""

    def __init__(
        self,
        request_id: int,
        animation: ParsedAnimation,
        models: tuple[ParticleModel, ...],
        adapter: MinecraftVersionAdapter,
        orientation: OrientationMode,
        force: bool,
    ) -> None:
        super().__init__()
        self.request_id = request_id
        self.animation = animation
        self.models = models
        self.adapter = adapter
        self.orientation = orientation
        self.force = force
        self.signals = _PredictionSignals()

    @Slot()
    def run(self) -> None:
        try:
            renderer = MinecraftRenderer(self.adapter)
            rendered_frames = tuple(
                tuple(
                    renderer.render(model, self.orientation, self.force)
                )
                for model in self.models
            )
            prediction = predict_generation(self.animation, rendered_frames)
            self.signals.completed.emit(
                self.request_id,
                prediction,
                None,
            )
        except Exception as error:
            self.signals.completed.emit(
                self.request_id,
                None,
                error,
            )


class MainWindow(QMainWindow):
    """Desktop user interface for image import and datapack export."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Minecraft 粒子图片函数包生成器 v{APP_VERSION}")
        self.resize(1360, 820)
        self._image_path: Path | None = None
        self._preview_pixmap: QPixmap | None = None
        self._animation: ParsedAnimation | None = None
        self._models_per_frame: tuple[ParticleModel, ...] = ()
        self._prediction: GenerationPrediction | None = None
        self._prediction_request = 0
        self._prediction_workers: dict[int, _PredictionWorker] = {}
        self._thread_pool = QThreadPool(self)
        self._thread_pool.setMaxThreadCount(1)
        self._image_preview_dialog = ImagePreviewDialog(self)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(250)
        self._preview_timer.timeout.connect(self._refresh_preview_and_prediction)
        try:
            self._config = load_config()
        except (OSError, ValueError):
            logger.exception("Unable to load user configuration")
            self._config = AppConfig()
            QMessageBox.warning(
                self,
                "配置读取失败",
                "无法读取保存的用户设置，将使用默认设置。"
                "关闭程序时会尝试保存为新配置。",
            )

        self._create_widgets()
        self._create_layout()
        self._restore_config()
        self._connect_signals()

    def _create_widgets(self) -> None:
        self.preview = QLabel("请导入 PNG 图片")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(360, 360)
        self.preview.setStyleSheet(
            "QLabel { background: #20242b; color: #d7dce2; "
            "border: 1px solid #505762; }"
        )
        self.simulation_preview = ParticleSimulationWidget()
        self.viewport = ParticleViewport()
        self.image_status = QLabel("尚未导入图片")
        self.import_button = QPushButton("导入 PNG/GIF/APNG 图片…")
        self.open_preview_button = QPushButton("打开图片预览窗口")

        self.particle_combo = QComboBox()
        particle_labels = {
            "dust": "Dust（保留像素颜色）",
            "flame": "Flame（忽略像素颜色）",
            "cloud": "Cloud（忽略像素颜色）",
            "end_rod": "End Rod（忽略像素颜色）",
        }
        for particle in SUPPORTED_PARTICLES:
            self.particle_combo.addItem(particle_labels[particle], particle)

        self.scale_spin = self._decimal_spin(0.05, 8.0, 1.0, 0.05, 2)
        self.spacing_spin = self._decimal_spin(0.01, 100.0, 0.25, 0.05, 2)
        self.size_spin = self._decimal_spin(0.01, 4.0, 1.0, 0.1, 2)
        self.offset_spins = [
            self._decimal_spin(-30_000, 30_000, 0, 0.1, 2)
            for _ in range(3)
        ]
        self.rotation_spins = [
            self._decimal_spin(-3600, 3600, 0, 5, 1)
            for _ in range(3)
        ]
        self.model_scale_spins = [
            self._decimal_spin(0.01, 100, 1, 0.1, 2)
            for _ in range(3)
        ]
        self.alpha_spin = self._decimal_spin(0, 1, 1, 0.05, 2)
        self.pivot_combo = QComboBox()
        self.pivot_combo.addItem("左下角（默认原点）", PivotMode.LOWER_LEFT.value)
        self.pivot_combo.addItem("中心点", PivotMode.CENTER.value)
        self.pivot_combo.addItem("自定义 Pivot", PivotMode.CUSTOM.value)
        self.custom_pivot_spins = [
            self._decimal_spin(-100_000, 100_000, 0, 0.1, 2)
            for _ in range(3)
        ]
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItem("固定世界方向", OrientationMode.WORLD_FIXED.value)
        self.orientation_combo.addItem("跟随函数执行者朝向", OrientationMode.EXECUTOR.value)
        self.orientation_combo.addItem("跟随最近玩家视角", OrientationMode.PLAYER_VIEW.value)
        self.orientation_combo.setToolTip(
            "执行者朝向来自 function 的当前执行上下文；"
            "玩家视角模式会选取执行位置最近的玩家。"
        )
        self.force_combo = QComboBox()
        self.force_combo.addItem("Normal（普通可见范围）", False)
        self.force_combo.addItem("Force（强制显示）", True)
        self.namespace_edit = QLineEdit("particle_image")
        self.function_edit = QLineEdit("draw")
        self.version_combo = QComboBox()
        for version_name in SUPPORTED_VERSIONS:
            self.version_combo.addItem(
                f"Minecraft Java Edition {version_name}",
                version_name,
            )
        self.performance_combo = QComboBox()
        for mode in PerformanceMode:
            self.performance_combo.addItem(performance_label(mode), mode.value)
        self.prediction_label = QLabel(
            "导入图片后显示粒子数、mcfunction 大小和执行风险。"
        )
        self.prediction_label.setWordWrap(True)
        self.prediction_label.setStyleSheet(
            "QLabel { padding: 8px; background: #252b34; color: #e2e8f0; }"
        )
        self.generate_button = QPushButton("生成 ZIP 函数包…")
        self.generate_button.setEnabled(False)
        self.hint = QLabel(
            "透明度为 0 的像素会跳过；半透明像素按可见像素处理。"
            "Dust 保留 RGB 并使用粒子大小，其他粒子类型不支持像素颜色。"
        )
        self.hint.setWordWrap(True)

    @staticmethod
    def _decimal_spin(
        minimum: float,
        maximum: float,
        value: float,
        step: float,
        decimals: int,
    ) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setSingleStep(step)
        spin.setDecimals(decimals)
        return spin

    def _create_layout(self) -> None:
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)
        self.preview_tabs = QTabWidget()
        self.preview_tabs.addTab(self.preview, "图片")
        self.preview_tabs.addTab(self.simulation_preview, "粒子模拟")
        self.preview_tabs.addTab(self.viewport, "3D 模型编辑器")
        image_layout.addWidget(self.preview_tabs, stretch=1)
        image_layout.addWidget(self.image_status)
        image_layout.addWidget(self.open_preview_button)
        image_layout.addWidget(self.import_button)

        settings = QGroupBox("生成设置")
        form = QFormLayout(settings)
        form.addRow("Minecraft 版本", self.version_combo)
        form.addRow("粒子类型", self.particle_combo)
        form.addRow("性能模式", self.performance_combo)
        form.addRow("图片缩放倍率", self.scale_spin)
        form.addRow("粒子间距（方块）", self.spacing_spin)
        form.addRow("粒子大小（仅 Dust）", self.size_spin)

        offset_widget = QWidget()
        offset_layout = QHBoxLayout(offset_widget)
        offset_layout.setContentsMargins(0, 0, 0, 0)
        for axis, spin in zip("XYZ", self.offset_spins):
            offset_layout.addWidget(QLabel(axis))
            offset_layout.addWidget(spin)
        form.addRow("执行位置偏移", offset_widget)
        form.addRow("模型旋转（XYZ°）", self._axis_widget(self.rotation_spins))
        form.addRow("模型缩放（XYZ）", self._axis_widget(self.model_scale_spins))
        form.addRow("粒子透明度", self.alpha_spin)
        form.addRow("模型 Pivot", self.pivot_combo)
        form.addRow("自定义 Pivot（XYZ）", self._axis_widget(self.custom_pivot_spins))
        form.addRow("朝向模式", self.orientation_combo)
        form.addRow("粒子可见范围", self.force_combo)
        form.addRow("命名空间", self.namespace_edit)
        form.addRow("函数名称", self.function_edit)

        settings_panel = QWidget()
        settings_layout = QVBoxLayout(settings_panel)
        settings_layout.addWidget(settings)
        settings_layout.addWidget(QLabel("生成前预测"))
        settings_layout.addWidget(self.prediction_label)
        settings_layout.addWidget(self.hint)
        settings_layout.addStretch(1)
        settings_layout.addWidget(self.generate_button)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.addWidget(image_panel, stretch=3)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setWidget(settings_panel)
        root_layout.addWidget(settings_scroll, stretch=2)
        self.setCentralWidget(root)

    @staticmethod
    def _axis_widget(spins: list[QDoubleSpinBox]) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        for axis, spin in zip("XYZ", spins):
            layout.addWidget(QLabel(axis))
            layout.addWidget(spin)
        return widget

    def _connect_signals(self) -> None:
        self.import_button.clicked.connect(self._select_image)
        self.open_preview_button.clicked.connect(self._open_image_preview)
        self.generate_button.clicked.connect(self._generate_datapack)
        self.particle_combo.currentIndexChanged.connect(self._update_size_state)
        self.performance_combo.currentIndexChanged.connect(self._reload_image)
        self.scale_spin.valueChanged.connect(self._reload_image)
        for combo in (
            self.particle_combo,
            self.version_combo,
            self.force_combo,
            self.orientation_combo,
            self.pivot_combo,
        ):
            combo.currentIndexChanged.connect(self._schedule_preview_refresh)
        for control in (
            self.spacing_spin,
            self.size_spin,
            self.alpha_spin,
            *self.offset_spins,
            *self.rotation_spins,
            *self.model_scale_spins,
            *self.custom_pivot_spins,
        ):
            control.valueChanged.connect(self._schedule_preview_refresh)
        self._update_size_state()

    def _restore_config(self) -> None:
        """Restore persisted settings and the previous image when available."""
        controls = (
            (self.version_combo, self._config.minecraft_version),
            (self.particle_combo, self._config.particle),
            (self.force_combo, self._config.force),
            (self.performance_combo, self._config.performance_mode),
            (self.pivot_combo, self._config.pivot_mode),
            (self.orientation_combo, self._config.orientation_mode),
        )
        for combo, value in controls:
            index = combo.findData(value)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                logger.warning("Ignoring unsupported saved value %r", value)

        for control, value in (
            (self.scale_spin, self._config.scale),
            (self.spacing_spin, self._config.spacing),
            (self.size_spin, self._config.size),
            (self.offset_spins[0], self._config.offset_x),
            (self.offset_spins[1], self._config.offset_y),
            (self.offset_spins[2], self._config.offset_z),
            (self.rotation_spins[0], self._config.rotation_x),
            (self.rotation_spins[1], self._config.rotation_y),
            (self.rotation_spins[2], self._config.rotation_z),
            (self.model_scale_spins[0], self._config.model_scale_x),
            (self.model_scale_spins[1], self._config.model_scale_y),
            (self.model_scale_spins[2], self._config.model_scale_z),
            (self.alpha_spin, self._config.alpha),
            (self.custom_pivot_spins[0], self._config.pivot_x),
            (self.custom_pivot_spins[1], self._config.pivot_y),
            (self.custom_pivot_spins[2], self._config.pivot_z),
        ):
            control.setValue(value)
        self.namespace_edit.setText(self._config.namespace)
        self.function_edit.setText(self._config.function_name)
        self._update_size_state()

        if self._config.last_image:
            saved_image = Path(self._config.last_image)
            if saved_image.is_file():
                pixmap = QPixmap(str(saved_image))
                if not pixmap.isNull():
                    self._image_path = saved_image
                    self._reload_image()
                    return
            logger.info(
                "Previously selected image is no longer available: %s",
                saved_image,
            )

    def _set_image(self, image_path: Path) -> None:
        self._image_path = image_path
        self._reload_image()

    def _select_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "选择 PNG/GIF/APNG 图片",
            "",
            "图片 (*.png *.apng *.gif);;所有文件 (*.*)",
        )
        if not filename:
            return
        self._set_image(Path(filename))

    def _selected_mode(self) -> PerformanceMode:
        return PerformanceMode(self.performance_combo.currentData())

    def _reload_image(self) -> None:
        """Reparse the selected image when scale or quality mode changes."""
        if self._image_path is None:
            return
        try:
            animation = ImageParser.parse_animation(
                self._image_path,
                scale=self.scale_spin.value(),
                mode=self._selected_mode(),
            )
        except (OSError, ValueError) as error:
            logger.exception("Unable to load image or animation")
            self._prediction_request += 1
            self._animation = None
            self._models_per_frame = ()
            self._prediction = None
            self.viewport.set_model(None)
            self.generate_button.setEnabled(False)
            self.simulation_preview.set_animation(
                None,
                self.particle_combo.currentData(),
                self.spacing_spin.value(),
                self.size_spin.value(),
                tuple(spin.value() for spin in self.offset_spins),
            )
            self.prediction_label.setText(f"图片读取失败：{error}")
            QMessageBox.warning(self, "无法读取图片", str(error))
            return

        self._animation = animation
        self.generate_button.setEnabled(True)
        self.preview.setText("")
        self._preview_pixmap = parsed_image_pixmap(animation.frames[0])
        self._refresh_preview()
        self.image_status.setText(
            f"{self._image_path.name} — "
            f"{animation.frames[0].width} × {animation.frames[0].height}，"
            f"{animation.frame_count} 帧，{animation.total_particles:,} 个可见像素"
        )
        self._image_preview_dialog.set_animation(str(self._image_path), animation)
        self._schedule_preview_refresh()

    def _open_image_preview(self) -> None:
        if self._animation is None:
            QMessageBox.information(
                self,
                "尚未导入图片",
                "请先导入 PNG、GIF 或 APNG 图片。",
            )
            return
        self._image_preview_dialog.show()
        self._image_preview_dialog.raise_()
        self._image_preview_dialog.activateWindow()

    def _refresh_preview(self) -> None:
        if self._preview_pixmap is not None:
            self.preview.setPixmap(
                self._preview_pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh_preview()

    def _update_size_state(self) -> None:
        self.size_spin.setEnabled(self.particle_combo.currentData() == "dust")
        if self._animation is not None:
            self._schedule_preview_refresh()

    def _schedule_preview_refresh(self) -> None:
        if self._animation is None:
            return
        self._prediction_request += 1
        self._prediction = None
        self.generate_button.setEnabled(False)
        self.prediction_label.setText("正在计算模型变换和生成风险…")
        self._models_per_frame = self._build_models()
        self.viewport.set_model(
            self._models_per_frame[0] if self._models_per_frame else None
        )
        self.simulation_preview.set_animation(
            self._animation,
            self.particle_combo.currentData(),
            self.spacing_spin.value(),
            self.size_spin.value(),
            tuple(spin.value() for spin in self.offset_spins),
        )
        self._preview_timer.start()

    def _build_models(self) -> tuple[ParticleModel, ...]:
        if self._animation is None:
            return ()
        offset = tuple(spin.value() for spin in self.offset_spins)
        rotation = tuple(spin.value() for spin in self.rotation_spins)
        scale = tuple(spin.value() for spin in self.model_scale_spins)
        custom_pivot = tuple(spin.value() for spin in self.custom_pivot_spins)
        pivot_mode = PivotMode(self.pivot_combo.currentData())
        models: list[ParticleModel] = []
        for frame in self._animation.frames:
            model = ParticleModel.from_image(
                frame,
                spacing=self.spacing_spin.value(),
                particle_size=self.size_spin.value(),
            )
            model.particle_type = self.particle_combo.currentData()
            model.transform = Transform(
                position_offset=offset,
                rotation=rotation,
                scale=scale,
            )
            model.pivot_mode = pivot_mode
            model.custom_pivot = custom_pivot
            alpha_multiplier = self.alpha_spin.value()
            for particle in model.particles:
                particle.alpha *= alpha_multiplier
            models.append(model)
        return tuple(models)

    def _refresh_preview_and_prediction(self) -> None:
        if self._animation is None or not self._models_per_frame:
            return
        try:
            adapter = create_adapter(self.version_combo.currentData())
            worker = _PredictionWorker(
                request_id=self._prediction_request,
                animation=self._animation,
                models=self._models_per_frame,
                adapter=adapter,
                orientation=OrientationMode(self.orientation_combo.currentData()),
                force=self.force_combo.currentData(),
            )
            worker.signals.completed.connect(self._prediction_ready)
            self._prediction_workers[self._prediction_request] = worker
            self._thread_pool.start(worker)
        except (OSError, ValueError):
            logger.exception("Unable to start generation prediction")
            self.prediction_label.setText("无法启动预测任务，请查看应用日志。")
            return

    @Slot(int, object, object)
    def _prediction_ready(
        self,
        request_id: int,
        prediction: object,
        error: object,
    ) -> None:
        self._prediction_workers.pop(request_id, None)
        if request_id != self._prediction_request:
            return
        if error is not None:
            if isinstance(error, BaseException):
                logger.error(
                    "Unable to calculate generation prediction",
                    exc_info=(type(error), error, error.__traceback__),
                )
            else:
                logger.error("Prediction worker failed: %s", error)
            self._prediction = None
            self.prediction_label.setText(f"无法预测：{error}")
            self.generate_button.setEnabled(False)
            return

        if not isinstance(prediction, GenerationPrediction):
            logger.error("Prediction worker returned invalid result types")
            self.prediction_label.setText("预测结果无效，请查看应用日志。")
            self.generate_button.setEnabled(False)
            return
        self._prediction = prediction
        self.generate_button.setEnabled(True)
        self.prediction_label.setText(
            f"帧数：{self._animation.frame_count:,}\n"
            f"粒子数量：{prediction.particle_count:,}（单帧最多 "
            f"{prediction.largest_frame_particles:,}）\n"
            f"mcfunction 估算大小：{prediction.mcfunction_bytes:,} 字节\n"
            f"执行风险：{prediction.risk_message}"
        )
        color = {
            "low": "#245c3d",
            "medium": "#795a20",
            "high": "#7d3030",
        }[prediction.risk_level]
        self.prediction_label.setStyleSheet(
            f"QLabel {{ padding: 8px; background: {color}; color: #ffffff; }}"
        )

    def _generate_datapack(self) -> None:
        if self._image_path is None or self._animation is None:
            QMessageBox.warning(self, "尚未导入图片", "请先导入一张 PNG 图片。")
            return

        if not self._models_per_frame or self._prediction is None:
            QMessageBox.warning(self, "尚未完成预测", "请等待生成预测完成后重试。")
            return
        if self._prediction.risk_level == "high":
            answer = QMessageBox.warning(
                self,
                "高执行风险",
                f"{self._prediction.risk_message}\n"
                "建议切换到低性能模式或缩小图片。仍要继续生成吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        suggested_name = f"{self._image_path.stem}_datapack.zip"
        output, _ = QFileDialog.getSaveFileName(
            self,
            "保存函数包",
            str(self._image_path.with_name(suggested_name)),
            "ZIP 函数包 (*.zip)",
        )
        if not output:
            return
        if not output.lower().endswith(".zip"):
            output += ".zip"

        try:
            adapter = create_adapter(self.version_combo.currentData())
            renderer = MinecraftRenderer(adapter)
            frame_commands = tuple(
                tuple(
                    renderer.render(
                        model,
                        OrientationMode(self.orientation_combo.currentData()),
                        self.force_combo.currentData(),
                    )
                )
                for model in self._models_per_frame
            )
            namespace = self.namespace_edit.text().strip()
            function_name = self.function_edit.text().strip()
            if self._animation.frame_count > 1:
                executor_tag = DatapackBuilder.animation_tag(
                    namespace,
                    function_name,
                )
                durations_ticks = tuple(
                    max(1, round(duration / 50))
                    for duration in self._animation.durations_ms
                )
                archive_path = DatapackBuilder.build_animation(
                    output_path=output,
                    namespace=namespace,
                    function_name=function_name,
                    frames=frame_commands,
                    durations_ticks=durations_ticks,
                    adapter=adapter,
                    executor_tag=executor_tag,
                )
            else:
                archive_path = DatapackBuilder.build(
                    output_path=output,
                    namespace=namespace,
                    function_name=function_name,
                    commands=frame_commands[0],
                    adapter=adapter,
                )
        except (OSError, ValueError) as error:
            logger.exception("Datapack generation failed")
            QMessageBox.critical(self, "生成失败", str(error))
            return
        except Exception:
            logger.exception("Unexpected error during datapack generation")
            QMessageBox.critical(
                self,
                "生成失败",
                "发生未预期错误。请查看应用日志以获取详细信息。",
            )
            return

        self.image_status.setText(
            f"{self._image_path.name} — "
            f"{self._prediction.particle_count:,} 个粒子"
        )
        if self._animation.frame_count > 1:
            start_id = f"{namespace}:{function_name}/animation/start"
            stop_id = f"{namespace}:{function_name}/animation/stop"
            usage = (
                f"循环播放：/function {start_id}（需由玩家执行）\n"
                f"停止播放：/function {stop_id}"
            )
        else:
            usage = f"在游戏中执行：/function {namespace}:{function_name}"
        logger.info(
            "Datapack exported to %s (%d particle commands)",
            archive_path,
            self._prediction.particle_count,
        )
        QMessageBox.information(
            self,
            "生成完成",
            f"已生成 {self._prediction.particle_count:,} 条粒子命令：\n"
            f"{archive_path}\n\n{usage}\n"
            f"目标版本：Minecraft Java Edition {adapter.version_name}",
        )

    def _current_config(self) -> AppConfig:
        return AppConfig(
            minecraft_version=self.version_combo.currentData(),
            particle=self.particle_combo.currentData(),
            scale=self.scale_spin.value(),
            spacing=self.spacing_spin.value(),
            size=self.size_spin.value(),
            offset_x=self.offset_spins[0].value(),
            offset_y=self.offset_spins[1].value(),
            offset_z=self.offset_spins[2].value(),
            force=self.force_combo.currentData(),
            namespace=self.namespace_edit.text(),
            function_name=self.function_edit.text(),
            last_image=str(self._image_path) if self._image_path else "",
            performance_mode=self.performance_combo.currentData(),
            rotation_x=self.rotation_spins[0].value(),
            rotation_y=self.rotation_spins[1].value(),
            rotation_z=self.rotation_spins[2].value(),
            model_scale_x=self.model_scale_spins[0].value(),
            model_scale_y=self.model_scale_spins[1].value(),
            model_scale_z=self.model_scale_spins[2].value(),
            alpha=self.alpha_spin.value(),
            pivot_mode=self.pivot_combo.currentData(),
            pivot_x=self.custom_pivot_spins[0].value(),
            pivot_y=self.custom_pivot_spins[1].value(),
            pivot_z=self.custom_pivot_spins[2].value(),
            orientation_mode=self.orientation_combo.currentData(),
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            path = save_config(self._current_config())
            logger.info("User configuration saved to %s", path)
        except (OSError, ValueError):
            logger.exception("Unable to save user configuration")
            QMessageBox.warning(
                self,
                "设置保存失败",
                "无法保存用户设置。请检查用户目录权限，并查看应用日志。",
            )
        event.accept()
