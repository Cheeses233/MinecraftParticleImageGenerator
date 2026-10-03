"""Rotating per-user log configuration and uncaught exception reporting."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app_info import APP_NAME


def setup_logging() -> Path:
    """Set up a rotating log file under the current user's Local AppData."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise OSError("无法定位 Windows Local AppData 目录，不能创建错误日志。")
    log_directory = Path(local_app_data) / APP_NAME / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "application.log"

    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    logging.captureWarnings(True)
    return log_path


def install_exception_hook() -> None:
    """Write uncaught Python exceptions to the rotating application log."""

    def handle_exception(
        exception_type: type[BaseException],
        exception: BaseException,
        traceback: object,
    ) -> None:
        if issubclass(exception_type, KeyboardInterrupt):
            sys.__excepthook__(exception_type, exception, traceback)
            return
        logging.getLogger("uncaught").critical(
            "Uncaught exception", exc_info=(exception_type, exception, traceback)
        )

    sys.excepthook = handle_exception
