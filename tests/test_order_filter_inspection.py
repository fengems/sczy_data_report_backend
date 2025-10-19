"""
订单中心筛选项检查脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.base import BaseCrawler
from app.crawlers.auth import ERPAuthCrawler
from app.utils.logger import get_logger


class OrderFilterInspector(BaseCrawler):
    """订单筛选项检查器"""

    def __init__(self):
        super().__init__("order_inspector")

    async def login(self) -> bool:
        """使用ERP认证模块登录"""
        auth_crawler = ERPAuthCrawler()
        auth_crawler.browser = self.browser
        auth_crawler.context = self.context
        auth_crawler.page = self.page
        return await auth_crawler.login()

    async def crawl_data(self, params):
        """实现抽象方法"""
        return await self.inspect_filters()

    async def inspect_filters(self):
        """检查订单页面的筛选项"""
        self.logger.info("开始检查订单页面筛选项...")

        # 导航到订单页面
        await self.navigate_to("/cc_sssp/superAdmin/viewCenter/v1/order/list")

        # 打开高级筛选
        base_filter = await self.page.wait_for_selector(".base-filter", timeout=10000)
        filter_advance = await base_filter.query_selector(".filter__advance-trigger")

        if filter_advance:
            text_content = await filter_advance.text_content()
            if text_content and text_content.strip() == "高级筛选":
                await filter_advance.click()
                await asyncio.sleep(0.5)
                self.logger.info("已展开高级筛选")

        # 查找所有筛选项
        filter_cols = await self.page.query_selector_all(".filter__col")
        self.logger.info(f"找到 {len(filter_cols)} 个筛选项")

        # 打印所有筛选项的标签
        for i, col in enumerate(filter_cols):
            # 尝试多种方式获取标签文本
            label_element = await col.query_selector("label")
            span_element = await col.query_selector("span")
            div_element = await col.query_selector("div")

            label_text = ""
            if label_element:
                label_text = await label_element.text_content()
            elif span_element:
                label_text = await span_element.text_content()
            elif div_element:
                label_text = await div_element.text_content()

            if label_text and len(label_text.strip()) > 0:
                self.logger.info(f"筛选项 {i+1}: '{label_text.strip()}'")

                # 查看这个筛选项下是否有input元素
                input_element = await col.query_selector("input")
                if input_element:
                    input_type = await input_element.get_attribute("type")
                    input_placeholder = await input_element.get_attribute("placeholder")
                    self.logger.info(f"  - input类型: {input_type}, placeholder: {input_placeholder}")

                # 查看是否还有其他span元素
                span_elements = await col.query_selector_all("span")
                for j, span in enumerate(span_elements):
                    span_text = await span.text_content()
                    if span_text and len(span_text.strip()) > 0:
                        self.logger.info(f"  - span{j+1}文本: '{span_text.strip()}'")
            else:
                self.logger.info(f"筛选项 {i+1}: (无文本标签)")


async def main():
    """主函数"""
    logger = get_logger("filter_inspector")

    inspector = OrderFilterInspector()

    try:
        async with inspector.browser_session():
            # 等待登录
            if not await inspector.check_login_status():
                logger.info("需要登录...")
                await inspector.login()

            await inspector.inspect_filters()
            logger.info("筛选项检查完成")
    except Exception as e:
        logger.error(f"检查失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())