#!/usr/bin/env python3
"""
商品档案爬虫运行脚本
用于快速测试商品档案导出功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置工作目录到项目根目录，确保能找到.env文件
os.chdir(project_root)

from app.crawlers.goods_archive import GoodsArchiveCrawler
from app.utils.logger import get_logger


async def main():
    """
    运行商品档案爬虫
    """
    logger = get_logger("run_goods_archive")

    try:
        logger.info("🚀 启动商品档案爬虫...")

        # 创建爬虫实例
        crawler = GoodsArchiveCrawler()

        # 运行爬虫
        result = await crawler.run()

        logger.info(f"✅ 商品档案导出成功！")
        logger.info(f"📁 下载文件路径: {result}")

    except Exception as e:
        logger.error(f"❌ 商品档案导出失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())