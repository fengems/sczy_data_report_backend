#!/usr/bin/env python3
"""
直接下载方式示例
展示如何使用重构后的任务中心工具处理直接导出的情况
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from app.crawlers.utils import wait_for_export_task
from app.utils.logger import get_logger


async def example_direct_download():
    """
    示例：直接下载方式（适用于不弹出任务中心的导出）
    """
    logger = get_logger("direct_download_example")

    # 假设已经有了page对象，这里只是示例用法
    # 实际使用中，page对象来自BaseCrawler或其他地方

    logger.info("示例：使用直接下载方式")

    # 方式1: 使用便捷函数（推荐）
    download_path = await wait_for_export_task(
        page=page,  # 假设的page对象
        filename="直接导出文件",
        timeout=60,
        use_task_center=False  # 关键：使用直接下载模式
    )

    logger.info(f"直接下载完成: {download_path}")


async def example_task_center_download():
    """
    示例：任务中心方式（适用于弹出任务中心的大文件导出）
    """
    logger = get_logger("task_center_example")

    logger.info("示例：使用任务中心方式")

    # 方式2: 使用任务中心模式
    download_path = await wait_for_export_task(
        page=page,  # 假设的page对象
        filename="任务中心文件",
        timeout=300,
        use_task_center=True  # 关键：使用任务中心模式
    )

    logger.info(f"任务中心下载完成: {download_path}")


async def example_task_center_class():
    """
    示例：直接使用TaskCenterUtils类
    """
    logger = get_logger("task_center_class_example")

    # 创建工具实例
    task_utils = TaskCenterUtils(page)  # 假设的page对象

    # 根据需要选择下载方式
    if needs_task_center:  # 假设的判断条件
        download_path = await task_utils.wait_for_export_task(
            filename="文件",
            timeout=300,
            use_task_center=True
        )
    else:
        download_path = await task_utils.wait_for_export_task(
            filename="文件",
            timeout=60,
            use_task_center=False
        )

    logger.info(f"下载完成: {download_path}")


# 使用建议
"""
使用建议：

1. 大文件导出（通常弹出任务中心）：
   use_task_center=True
   timeout=300  # 5分钟

2. 小文件导出（通常直接下载）：
   use_task_center=False
   timeout=60   # 1分钟

3. 不确定情况时：
   优先使用 use_task_center=True
   如果发现没有任务中心弹窗，再改为 use_task_center=False

4. 统一项目导出逻辑：
   推荐所有导出功能都使用相同的接口，通过 use_task_center 参数控制
   这样可以保持代码的一致性和可维护性
"""