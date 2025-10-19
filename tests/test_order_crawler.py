"""
订单中心爬虫测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.order import OrderCrawler
from app.utils.logger import get_logger


async def test_order_crawler():
    """
    测试订单中心爬虫功能
    """
    logger = get_logger("test_order")

    try:
        logger.info("=" * 50)
        logger.info("开始测试订单中心爬虫")
        logger.info("=" * 50)

        # 创建爬虫实例
        crawler = OrderCrawler()

        # 测试参数1：使用发货日期
        logger.info("测试场景1：使用发货日期筛选")
        params1 = {
            "delivery_date_range": ["2025-10-01", "2025-10-15"],
            "export_fields": ["订单号", "客户名称", "订单时间", "发货时间", "线路名称", "业务员"]
        }

        # 运行爬虫
        result = await crawler.run(params1)

        logger.info(f"测试场景1完成，下载文件: {result}")

        # 等待一段时间再进行下一个测试
        await asyncio.sleep(2)

        # 测试参数2：使用下单时间（测试互斥逻辑）
        logger.info("测试场景2：使用下单时间筛选")
        params2 = {
            "order_time_range": ["2025-10-01 00:00", "2025-10-15 00:00"]
            # 不传导出字段，使用默认字段
        }

        # 运行爬虫
        result2 = await crawler.run(params2)

        logger.info(f"测试场景2完成，下载文件: {result2}")

        return True

    except Exception as e:
        logger.error(f"订单爬虫测试失败: {str(e)}")
        return False


async def main():
    """
    主测试函数
    """
    logger = get_logger("test_main")

    logger.info("启动订单中心爬虫测试...")

    success = await test_order_crawler()

    if success:
        logger.info("✅ 订单中心爬虫测试通过")
    else:
        logger.error("❌ 订单中心爬虫测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())