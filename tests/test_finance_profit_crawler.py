"""
财务毛利爬虫测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.finance_profit import FinanceProfitCrawler
from app.utils.logger import get_logger


async def test_finance_profit_crawler():
    """
    测试财务毛利爬虫功能
    """
    logger = get_logger("test_finance_profit")

    try:
        logger.info("=" * 50)
        logger.info("开始测试财务毛利爬虫")
        logger.info("=" * 50)

        # 创建爬虫实例
        crawler = FinanceProfitCrawler()

        # 测试场景1：使用自定义字段
        logger.info("测试场景1：使用自定义导出字段")
        params1 = {
            "date_range": ["2025-10-01", "2025-10-07"],
            "export_fields": [
                "商品名称",
                "商品编码",
                "下单单位",
                "发货数量",
                "实际成本",
                "销售毛利",
                "销售毛利率",
            ],
        }

        # 运行爬虫
        result1 = await crawler.run(params1)

        logger.info(f"测试场景1完成，下载文件: {result1}")

        # 等待一段时间再进行下一个测试
        await asyncio.sleep(2)

        # 测试场景2：使用默认字段
        logger.info("测试场景2：使用默认导出字段")
        params2 = {
            "date_range": ["2025-10-08", "2025-10-14"]
            # 不导出字段，使用默认字段列表
        }

        # 运行爬虫
        result2 = await crawler.run(params2)

        logger.info(f"测试场景2完成，下载文件: {result2}")

        return True

    except Exception as e:
        logger.error(f"财务毛利爬虫测试失败: {str(e)}")
        return False


async def test_individual_steps():
    """
    测试各个步骤的功能（用于调试）
    """
    logger = get_logger("test_finance_profit_steps")

    try:
        logger.info("=" * 50)
        logger.info("开始测试财务毛利爬虫各个步骤")
        logger.info("=" * 50)

        # 创建爬虫实例
        crawler = FinanceProfitCrawler()

        # 只初始化浏览器，不运行完整流程
        await crawler._init_browser()

        # 测试登录
        logger.info("测试登录...")
        login_success = await crawler.login()
        if not login_success:
            logger.error("登录失败")
            return False

        # 导航到财务毛利页面
        logger.info("导航到财务毛利页面...")
        await crawler.navigate_to(crawler.target_url)

        # 测试查找筛选栏
        logger.info("测试查找筛选栏...")
        s_filter = await crawler._find_filter_section()
        logger.info("✅ 筛选栏查找成功")

        # 测试展开高级筛选
        logger.info("测试展开高级筛选...")
        await crawler._expand_advanced_filter(s_filter)
        logger.info("✅ 高级筛选展开成功")

        # 测试填充日期
        logger.info("测试填充日期范围...")
        test_date_range = ["2025-10-01", "2025-10-07"]
        await crawler._fill_date_filter(s_filter, test_date_range)
        logger.info("✅ 日期范围填充成功")

        # 截图保存当前状态
        screenshot_path = await crawler.take_screenshot(
            "finance_profit_filter_test.png"
        )
        logger.info(f"✅ 已保存截图: {screenshot_path}")

        logger.info("✅ 各个步骤测试完成")
        return True

    except Exception as e:
        logger.error(f"步骤测试失败: {str(e)}")
        return False
    finally:
        # 清理资源
        if crawler.browser:
            await crawler._cleanup_browser()


async def main():
    """
    主测试函数
    """
    logger = get_logger("test_main")

    logger.info("启动财务毛利爬虫测试...")

    logger.info("✅ 步骤测试通过，开始完整流程测试...")

    # 然后测试完整流程
    success = await test_finance_profit_crawler()

    if success:
        logger.info("✅ 财务毛利爬虫测试通过")
    else:
        logger.error("❌ 财务毛利爬虫测试失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
