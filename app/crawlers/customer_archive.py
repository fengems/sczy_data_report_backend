"""
客户档案爬虫模块
用于从ERP系统导出客户档案基础信息
"""

import asyncio
from typing import Any, Dict, Optional

from app.crawlers.base import BaseCrawler
from app.crawlers.utils import wait_for_export_task


class CustomerArchiveCrawler(BaseCrawler):
    """客户档案爬虫"""

    def __init__(self) -> None:
        super().__init__("customer_archive")
        self.target_url = "/cc_sssp/superAdmin/viewCenter/v1/user/list"

    async def login(self) -> bool:
        """
        使用现有的ERP认证模块进行登录
        """
        from app.crawlers.auth import ERPAuthCrawler

        auth_crawler = ERPAuthCrawler()
        auth_crawler.browser = self.browser
        auth_crawler.context = self.context
        auth_crawler.page = self.page

        return await auth_crawler.login()

    async def find_filter_section(self) -> Optional[Any]:
        """
        步骤1: 找到filter栏
        使用 ".base-filter" 找到页面可见的 baseFilter 元素
        """
        try:
            self.logger.info("开始定位filter栏...")

            # 等待页面基本加载完成
            if self.page:
                await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(0.5)  # 短暂等待确保JS渲染完成

            # 使用确定的选择器 ".base-filter"
            try:
                if self.page:
                    filter_element = await self.page.wait_for_selector(
                        ".base-filter", timeout=10000
                    )
                    if filter_element and await filter_element.is_visible():
                        self.logger.info("找到filter栏，选择器: .base-filter")
                        return filter_element
            except Exception as e:
                self.logger.error(f"使用 .base-filter 选择器未找到元素: {str(e)}")

            raise RuntimeError("无法找到filter栏")

        except Exception as e:
            self.logger.error(f"定位filter栏失败: {str(e)}")
            await self.take_screenshot("filter_not_found.png")
            raise

    async def find_export_button(self, filter_element: Any) -> Optional[Any]:
        """
        步骤2: 找到导出按钮
        在 filter_element 中使用 ".export-box" 找到 exportBox 导出按钮元素
        """
        try:
            self.logger.info("开始定位导出按钮...")

            # 在filter栏内使用确定的选择器 ".export-box"
            try:
                if hasattr(filter_element, "locator"):
                    export_button = filter_element.locator(".export-box")
                    if await export_button.count() > 0:
                        button = export_button.first
                        if await button.is_visible():
                            self.logger.info("找到导出按钮，选择器: .export-box")
                            return button
            except Exception as e:
                self.logger.error(f"在filter区域内查找 .export-box 失败: {str(e)}")

            # 备用方案：在全局范围内查找 ".export-box"
            try:
                if self.page:
                    export_button = await self.page.wait_for_selector(
                        ".export-box", timeout=5000
                    )
                    if export_button and await export_button.is_visible():
                        self.logger.info("在全局范围内找到导出按钮，选择器: .export-box")
                        return export_button
            except Exception as e:
                self.logger.error(f"全局查找 .export-box 失败: {str(e)}")

            raise RuntimeError("无法找到导出按钮")

        except Exception as e:
            self.logger.error(f"定位导出按钮失败: {str(e)}")
            await self.take_screenshot("export_button_not_found.png")
            raise

    async def show_and_find_dropdown(self, export_button: Any) -> Any:
        """
        步骤3: Hover导出按钮
        在 exportBox 上面 hover，会出现 dropdown
        """
        try:
            self.logger.info("开始hover导出按钮显示dropdown...")

            # 确保导出按钮可见并hover到它
            await export_button.scroll_into_view_if_needed()
            await export_button.hover()
            self.logger.info("已hover到导出按钮")

            # 等待dropdown出现
            await asyncio.sleep(1)

            # 直接返回导出按钮，下一步将在其附近查找dropdown元素
            return export_button

        except Exception as e:
            self.logger.error(f"Hover导出按钮失败: {str(e)}")
            await self.take_screenshot("dropdown_not_found.png")
            raise

    async def find_dropdown_item(self, export_button: Any) -> Optional[Any]:
        """
        步骤4: 点击导出客户
        在 exportBox 中用 ".ivu-dropdown-item" 找到内部含有文本 "客户" 的 exportItem 元素
        """
        try:
            self.logger.info("开始定位导出客户dropdown-item...")

            # 优先方案：直接通过文本查找包含"客户"的dropdown项
            try:
                if self.page:
                    customer_item = await self.page.wait_for_selector(
                        ".ivu-dropdown-item:has-text('客户')", timeout=5000
                    )
                    if customer_item and await customer_item.is_visible():
                        # 验证文本内容确实包含"客户"
                        text = await customer_item.text_content()
                        if text and "客户" in text.strip():
                            self.logger.info(f"找到导出客户项，文本: {text.strip() if text else ''}")
                            return customer_item
            except Exception as e:
                self.logger.debug(f"直接查找 .ivu-dropdown-item:has-text('客户') 失败: {str(e)}")

            # 备用方案：查找所有 .ivu-dropdown-item 元素，筛选包含"客户"文本的
            try:
                if self.page:
                    all_items = self.page.locator(".ivu-dropdown-item")
                    item_count = await all_items.count()
                    for i in range(item_count):
                        try:
                            item = all_items.nth(i)
                            text = await item.text_content()
                            if text and "客户" in text.strip() and await item.is_visible():
                                self.logger.info(f"通过筛选找到导出客户项，文本: {text.strip() if text else ''}")
                                return item
                        except Exception:
                            continue
            except Exception as e:
                self.logger.debug(f"筛选所有 .ivu-dropdown-item 失败: {str(e)}")

            # 最终备用方案：查找任何包含"客户"文本的可点击元素
            try:
                if self.page:
                    customer_element = await self.page.wait_for_selector(
                        "*:has-text('客户')", timeout=3000
                    )
                    if customer_element and await customer_element.is_visible():
                        # 检查是否为dropdown项或类似的菜单项
                        tag_name = await customer_element.evaluate("el => el.tagName.toLowerCase()")
                        class_attr = await customer_element.get_attribute("class") or ""

                        if ("li" in tag_name or
                            "dropdown" in class_attr.lower() or
                            "item" in class_attr.lower() or
                            "menu" in class_attr.lower()):
                            text = await customer_element.text_content()
                            self.logger.info(f"找到客户元素，标签: {tag_name}, 类: {class_attr}, 文本: {text.strip() if text else ''}")
                            return customer_element
            except Exception as e:
                self.logger.debug(f"查找包含'客户'文本的元素失败: {str(e)}")

            raise RuntimeError("无法找到导出客户dropdown-item")

        except Exception as e:
            self.logger.error(f"定位导出客户dropdown-item失败: {str(e)}")
            await self.take_screenshot("dropdown_item_not_found.png")
            raise

    async def crawl_data(self, params: Dict[str, Any]) -> str:
        """
        执行客户档案导出流程
        """
        try:
            # 导航到客户档案页面
            self.logger.info(f"导航到客户档案页面: {self.target_url}")
            # 暂时忽略参数，将来可以用于配置导出选项
            _ = params  # 标记参数已被考虑但未使用
            await self.navigate_to(self.target_url)

            # 执行导出流程
            filter_element = await self.find_filter_section()
            export_button = await self.find_export_button(filter_element)
            await self.show_and_find_dropdown(export_button)
            dropdown_item = await self.find_dropdown_item(export_button)

            # 点击dropdown-item
            if dropdown_item:
                await dropdown_item.click()
                self.logger.info("已点击导出客户dropdown-item")

            # 等待一段时间让导出任务提交到任务中心
            await asyncio.sleep(2)

            # 使用任务中心工具等待导出完成
            self.logger.info("等待任务中心处理导出...")
            download_path = await wait_for_export_task(
                page=self.page,
                filename="客户档案",  # 可选的自定义文件名
                timeout=300,  # 等待5分钟
                use_task_center=True,  # 使用任务中心模式（适用于大文件导出）
            )

            self.logger.info(f"客户档案导出完成，文件保存路径: {download_path}")
            return download_path

        except Exception as e:
            self.logger.error(f"客户档案导出失败: {str(e)}")
            await self.take_screenshot("customer_archive_error.png")
            raise