#!/usr/bin/env python3
"""
浏览器配置测试脚本
用于验证新的浏览器视口和调试功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from app.crawlers.base import BaseCrawler
from app.utils.logger import get_logger


class TestBrowserCrawler(BaseCrawler):
    """测试浏览器配置的爬虫"""

    def __init__(self):
        super().__init__("test_browser")

    async def login(self) -> bool:
        """测试不需要登录"""
        return True

    async def crawl_data(self, params) -> dict:
        """测试浏览器功能"""
        self.logger.info("开始测试浏览器配置...")

        # 测试窗口大小获取
        size = await self.get_window_size()
        self.logger.info(f"初始窗口大小: {size}")

        # 测试窗口大小调整
        await self.resize_window(1200, 800)
        new_size = await self.get_window_size()
        self.logger.info(f"调整后窗口大小: {new_size}")

        # 导航到测试页面
        await self.navigate_to("")

        # 等待页面加载
        await asyncio.sleep(3)

        # 获取最终窗口大小
        final_size = await self.get_window_size()
        self.logger.info(f"最终窗口大小: {final_size}")

        return {
            "initial_size": size,
            "adjusted_size": new_size,
            "final_size": final_size,
            "page_title": await self.page.title(),
            "page_url": self.page.url
        }


async def main():
    """主测试函数"""
    logger = get_logger("test_browser")

    try:
        logger.info("🚀 开始测试浏览器配置...")

        # 创建测试爬虫
        crawler = TestBrowserCrawler()

        # 运行测试
        result = await crawler.run()

        logger.info("✅ 浏览器配置测试完成")
        logger.info(f"测试结果: {result}")

    except Exception as e:
        logger.error(f"❌ 浏览器配置测试失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())