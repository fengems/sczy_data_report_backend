"""
日志配置模块
"""

import sys
from typing import Any, Optional

from loguru import logger

from app.config.settings import settings


def setup_logger() -> None:
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log_level,
        colorize=True,
    )

    # 添加文件处理器
    logger.add(
        settings.log_file,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    logger.info("Logger initialized successfully")


def get_logger(name: Optional[str] = None) -> Any:
    """获取logger实例"""
    if name:
        return logger.bind(name=name)
    return logger
