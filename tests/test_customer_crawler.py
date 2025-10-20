#!/usr/bin/env python3
"""
客户档案爬虫测试脚本
用于测试客户档案爬虫的基本功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.customer_archive import CustomerArchiveCrawler
from app.utils.logger import get_logger

logger = get_logger("test_customer_crawler")


async def test_customer_crawler():
    """测试客户档案爬虫"""
    try:
        logger.info("开始测试客户档案爬虫...")

        # 创建爬虫实例
        crawler = CustomerArchiveCrawler()

        # 运行爬虫（不需要参数）
        result = await crawler.run()

        logger.info(f"测试成功！导出文件路径: {result}")
        return result

    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(test_customer_crawler())
    print(f"客户档案导出完成: {result}")