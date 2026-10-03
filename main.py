"""Application entry point for the Minecraft particle image generator."""

from __future__ import annotations

import sys
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app_info import APP_NAME, APP_ORGANIZATION, APP_VERSION
from core.app_logging import install_exception_hook, setup_logging
from core.resource_paths import check_required_resources, resource_path
from ui.main_window import MainWindow


def main() -> int:
    """Create and run the desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_ORGANIZATION)

    try:
        setup_logging()
        install_exception_hook()
        check_required_resources()
        app.setWindowIcon(QIcon(str(resource_path("resources/app_icon.ico"))))
        window = MainWindow()
    except Exception as error:
        logging.getLogger(__name__).exception("Application startup failed")
        QMessageBox.critical(
            None,
            f"{APP_NAME} 启动失败",
            f"应用无法启动：\n{error}",
        )
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
