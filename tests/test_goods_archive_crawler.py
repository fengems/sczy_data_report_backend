"""
商品档案爬虫测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.goods_archive import GoodsArchiveCrawler
from app.utils.logger import get_logger


async def test_goods_archive_crawler():
    """
    测试商品档案爬虫功能
    """
    logger = get_logger("test_goods_archive")

    try:
        logger.info("=" * 50)
        logger.info("开始测试商品档案爬虫")
        logger.info("=" * 50)

        # 创建爬虫实例
        crawler = GoodsArchiveCrawler()

        # 运行爬虫
        result = await crawler.run()

        logger.info(f"爬虫测试完成，下载文件: {result}")
        return True

    except Exception as e:
        logger.error(f"爬虫测试失败: {str(e)}")
        return False


async def main():
    """
    主测试函数
    """
    logger = get_logger("test_main")

    logger.info("启动商品档案爬虫测试...")

    success = await test_goods_archive_crawler()

    if success:
        logger.info("✅ 商品档案爬虫测试通过")
    else:
        logger.error("❌ 商品档案爬虫测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())