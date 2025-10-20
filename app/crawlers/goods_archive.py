"""
商品档案爬虫模块
用于从ERP系统导出商品档案基础信息
"""

import asyncio
from typing import Any, Dict, Optional

from app.crawlers.base import BaseCrawler
from app.crawlers.utils import wait_for_export_task


class GoodsArchiveCrawler(BaseCrawler):
    """商品档案爬虫"""

    def __init__(self) -> None:
        super().__init__("goods_archive")
        self.target_url = "/cc_sssp/superAdmin/viewCenter/v1/goods/list"

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

    async def _safe_page_method(
        self, method_name: str, *args: Any, **kwargs: Any
    ) -> Optional[Any]:
        """安全调用page方法"""
        if not self.page:
            return None
        try:
            method = getattr(self.page, method_name)
            return await method(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error calling page.{method_name}: {e}")
            return None

    async def find_filter_section(self) -> Optional[Any]:
        """
        步骤1: 找到filter部分
        寻找页面上可见的 ".filter__button-wrap" 或者 ".filter__operation__btn-wrap"
        """
        try:
            self.logger.info("开始定位filter部分...")

            # 等待页面基本加载完成，不需要networkidle
            if self.page:
                await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(0.5)  # 短暂等待确保JS渲染完成

            # 尝试多个可能的filter选择器
            filter_selectors = [
                ".filter__operation__btn-wrap",  # 最可能的选择器放前面
                ".filter__button-wrap",
                ".filter-button-wrap",
                ".filter-operation-btn-wrap",
                "[class*='filter'][class*='button']",
                "[class*='filter'][class*='operation']",
            ]

            # 直接并行查找所有可能的filter元素
            filter_element = None

            for selector in filter_selectors:
                try:
                    element = await self._safe_page_method(
                        "wait_for_selector", selector, timeout=2000
                    )
                    if element and hasattr(element, "is_visible"):
                        is_visible = await element.is_visible()
                        if is_visible:
                            filter_element = element
                            self.logger.info(f"找到filter部分，选择器: {selector}")
                            break
                except Exception:
                    continue

            # 如果快速查找失败，尝试备用方案
            if not filter_element:
                self.logger.info("快速查找失败，尝试备用方案...")
                # 直接查找导出按钮，减少遍历所有按钮的开销
                try:
                    if self.page:
                        export_button = await self.page.wait_for_selector(
                            "button:has-text('导出')", timeout=3000
                        )
                        if export_button and await export_button.is_visible():
                            filter_element = export_button
                            self.logger.info("直接找到导出按钮，作为filter区域")
                except Exception:
                    pass

            if not filter_element:
                raise RuntimeError("无法找到filter部分")

            return filter_element

        except Exception as e:
            self.logger.error(f"定位filter部分失败: {str(e)}")
            await self.take_screenshot("filter_not_found.png")
            raise

    async def find_export_button(self, filter_element: Any) -> Optional[Any]:
        """
        步骤2: 找到导出按钮
        在filter部分找到文本为"导出"的按钮
        """
        try:
            self.logger.info("开始定位导出按钮...")

            # 在filter区域内查找导出按钮
            export_selectors = [
                "button:has-text('导出')",
                ".export-btn",
                "[class*='export']",
                "button[title*='导出']",
            ]

            export_button = None

            for selector in export_selectors:
                try:
                    # 如果在filter区域内查找
                    if filter_element and hasattr(filter_element, "locator"):
                        button = filter_element.locator(selector)
                        if await button.count() == 0:
                            button = None
                    else:
                        if self.page:
                            button = await self.page.wait_for_selector(
                                selector, timeout=5000
                            )

                    if button:
                        # 验证按钮文本
                        text = await button.text_content()
                        if text and text.strip().replace(" ", "") == "导出":
                            is_visible = await button.is_visible()
                            if is_visible:
                                export_button = button
                                self.logger.info(f"找到导出按钮，选择器: {selector}")
                                break
                except Exception:
                    continue

            # 备用方案：查找所有按钮，筛选文本内容
            if not export_button:
                self.logger.info("使用备用方案定位导出按钮...")
                if self.page:
                    all_buttons = self.page.locator("button")
                    button_count = await all_buttons.count()
                    for i in range(button_count):
                        try:
                            button = all_buttons.nth(i)
                            text = await button.text_content()
                            if text and text.strip().replace(" ", "") == "导出":
                                is_visible = await button.is_visible()
                                if is_visible:
                                    export_button = button
                                    self.logger.info("通过文本匹配找到导出按钮")
                                    break
                        except Exception:
                            continue

            if not export_button:
                raise RuntimeError("无法找到导出按钮")

            return export_button

        except Exception as e:
            self.logger.error(f"定位导出按钮失败: {str(e)}")
            await self.take_screenshot("export_button_not_found.png")
            raise

    async def show_and_find_dropdown(self, export_button: Any) -> Optional[Any]:
        """
        步骤3: 显示dropdown并找到dropdown元素
        在导出按钮上hover，显示dropdown后查找 ".ivu-select-dropdown" 元素
        """
        try:
            self.logger.info("开始显示并定位dropdown...")

            # 确保导出按钮可见并hover到它
            await export_button.scroll_into_view_if_needed()
            await export_button.hover()
            self.logger.info("已hover到导出按钮")

            # 短暂等待dropdown出现，不需要太长时间
            await asyncio.sleep(0.8)

            # 优先直接查找目标元素，而不是先找dropdown容器
            try:
                if self.page:
                    target_element = await self.page.wait_for_selector(
                        "text='基础信息导出'", timeout=3000
                    )
                    if target_element and await target_element.is_visible():
                        self.logger.info("直接找到目标元素，无需查找dropdown容器")
                        return target_element  # 直接返回目标元素
            except Exception:
                pass

            # 如果直接查找失败，再尝试查找dropdown容器
            dropdown_selectors = [
                ".ivu-dropdown",  # 最可能的dropdown选择器
                ".ivu-select-dropdown",
                ".ivu-dropdown-menu",
                "[class*='dropdown']",
                "[class*='select-dropdown']",
                ".ivu-dropdown-drop",
            ]

            dropdown_element = None

            for selector in dropdown_selectors:
                try:
                    if self.page:
                        element = await self.page.wait_for_selector(
                            selector, timeout=2000
                        )
                        if element and await element.is_visible():
                            dropdown_element = element
                            self.logger.info(f"找到dropdown元素，选择器: {selector}")
                            break
                except Exception:
                    continue

            if not dropdown_element:
                # 简化的备用方案：直接返回按钮，让下一步处理
                self.logger.info("未找到dropdown容器，将在下一步中直接查找目标元素")
                return export_button

            return dropdown_element

        except Exception as e:
            self.logger.error(f"定位dropdown失败: {str(e)}")
            await self.take_screenshot("dropdown_not_found.png")
            raise

    async def find_dropdown_item(self, dropdown_element: Any) -> Optional[Any]:
        """
        步骤4: 找到dropdown-item
        在dropdown中查找文本为"基础信息导出"的 li.ivu-dropdown-item 元素
        如果找不到dropdown容器，就直接在页面中查找目标元素
        """
        try:
            self.logger.info("开始定位dropdown-item...")

            # 如果上一步已经直接返回了目标元素，直接使用
            if dropdown_element and hasattr(dropdown_element, "text_content"):
                try:
                    text = await dropdown_element.text_content()
                    if text and "基础信息导出" in text.strip():
                        self.logger.info("使用上一步找到的目标元素")
                        return dropdown_element
                except Exception:
                    pass

            # 优先方案：直接文本查找，最快最准
            try:
                if self.page:
                    target_element = await self.page.wait_for_selector(
                        "text='基础信息导出'", timeout=3000
                    )
                    if target_element and await target_element.is_visible():
                        self.logger.info("直接找到'基础信息导出'元素")
                        return target_element
            except Exception:
                self.logger.info("直接查找失败，尝试备用方案...")

            # 简化的备用方案：只在dropdown_element内查找，避免全局搜索
            if dropdown_element and hasattr(dropdown_element, "locator"):
                try:
                    item = dropdown_element.locator("li:has-text('基础信息导出')")
                    if await item.count() > 0 and await item.is_visible():
                        self.logger.info("在dropdown容器内找到目标元素")
                        return item
                except Exception:
                    pass

            # 最终备用方案：快速全局查找，限制选择器数量
            quick_selectors = [
                "li:has-text('基础信息导出')",
                ".ivu-dropdown-item:has-text('基础信息导出')",
                "[class*='dropdown-item']:has-text('基础信息导出')",
            ]

            for selector in quick_selectors:
                try:
                    if self.page:
                        element = await self.page.wait_for_selector(
                            selector, timeout=2000
                        )
                        if element and await element.is_visible():
                            self.logger.info(f"通过选择器 {selector} 找到目标元素")
                            return element
                except Exception:
                    continue

            raise RuntimeError("无法找到'基础信息导出'dropdown-item")

        except Exception as e:
            self.logger.error(f"定位dropdown-item失败: {str(e)}")
            await self.take_screenshot("dropdown_item_not_found.png")
            raise

    async def handle_export_modal(self) -> bool:
        """
        步骤5: 处理导出modal弹窗
        点击dropdown-item后，在modal中找到并点击"确认导出"按钮
        增加多种处理策略：modal弹窗确认或直接下载
        """
        try:
            self.logger.info("开始处理导出modal弹窗...")

            # 短暂等待modal出现
            await asyncio.sleep(1)

            # 方案1: 快速查找modal弹窗并处理
            modal_element = await self._try_find_modal()
            if modal_element:
                return await self._handle_modal_confirmation(modal_element)

            # 方案2: 如果没有modal，可能直接开始下载，检查是否有下载开始
            self.logger.info("未找到modal弹窗，检查是否直接开始下载...")
            return await self._handle_direct_download()

        except Exception as e:
            self.logger.error(f"处理导出modal失败: {str(e)}")
            await self.take_screenshot("modal_error.png")
            raise

    async def _try_find_modal(self) -> Optional[Any]:
        """尝试查找modal弹窗"""
        # 查找modal - 使用更多的选择器
        modal_selectors = [
            ".ivu-modal",
            ".ivu-modal-confirm",
            ".ivu-modal-wrap",
            ".modal",
            ".modal-dialog",
            ".modal-content",
            "[class*='modal']",
            "[class*='Modal']",
            "[class*='popup']",
            "[class*='dialog']",
            ".el-dialog",
            ".el-message-box",
        ]

        for selector in modal_selectors:
            try:
                # 增加等待时间，给modal更多出现时间
                if self.page:
                    elements = self.page.locator(selector)
                    element_count = await elements.count()
                    for i in range(element_count):
                        element = elements.nth(i)
                        is_visible = await element.is_visible()
                        if is_visible:
                            self.logger.info(f"找到modal弹窗，选择器: {selector}")
                            return element
            except Exception:
                continue

        return None

    async def _handle_modal_confirmation(self, modal_element: Any) -> bool:
        """处理modal弹窗的确认操作"""
        # 优先查找最可能的确认按钮
        confirm_selectors = [
            "button:has-text('确认导出')",  # 最具体的选择器
            "button:has-text('确认')",
            ".ivu-btn-primary:has-text('确认')",
            ".btn-primary:has-text('确认')",
        ]

        confirm_button = None

        # 快速查找确认按钮，优先在modal内查找
        if hasattr(modal_element, "locator"):
            for selector in confirm_selectors:
                try:
                    button = modal_element.locator(selector)
                    if await button.count() > 0 and await button.is_visible():
                        confirm_button = button
                        text = await button.text_content()
                        self.logger.info(f"在modal内找到确认按钮: '{text if text else ''}'")
                        break
                except Exception:
                    continue

        # 如果modal内没找到，快速全局查找
        if not confirm_button:
            for selector in confirm_selectors:
                try:
                    if self.page:
                        button = await self.page.wait_for_selector(
                            selector, timeout=2000
                        )
                        if button and await button.is_visible():
                            confirm_button = button
                            text = await button.text_content()
                            self.logger.info(f"全局找到确认按钮: '{text if text else ''}'")
                            break
                except Exception:
                    continue

        if confirm_button:
            await confirm_button.click()
            self.logger.info("已点击确认导出按钮")
            return True
        else:
            self.logger.warning("未找到确认导出按钮，可能不需要确认")
            return False

    async def _handle_direct_download(self) -> bool:
        """处理直接下载情况（无modal弹窗）"""
        self.logger.info("检查是否直接开始下载...")

        # 短暂等待，看是否有下载开始
        await asyncio.sleep(1)

        # 检查页面状态，看是否有任何下载相关的提示
        try:
            # 查找可能的下载提示元素
            download_indicators = [
                ".ivu-message",
                ".ivu-notice",
                "[class*='message']",
                "[class*='notice']",
                "[class*='toast']",
                ".el-message",
                ".el-notification",
            ]

            for indicator in download_indicators:
                if self.page:
                    elements = self.page.locator(indicator)
                    element_count = await elements.count()
                    for i in range(element_count):
                        element = elements.nth(i)
                        if await element.is_visible():
                            text = await element.text_content()
                            if text and ("导出" in text or "下载" in text):
                                self.logger.info(f"发现下载提示: {text if text else ''}")
                                return True
        except Exception:
            pass

        # 即使没有找到任何提示，也认为可能正在后台下载
        self.logger.info("未找到明确的下载提示，但可能正在后台处理")
        return True

    async def crawl_data(self, params: Dict[str, Any]) -> str:
        """
        执行商品档案导出流程
        """
        try:
            # 导航到商品档案页面
            self.logger.info(f"导航到商品档案页面: {self.target_url}")
            # 暂时忽略参数，将来可以用于配置导出选项
            _ = params  # 标记参数已被考虑但未使用
            await self.navigate_to(self.target_url)

            # 执行导出流程
            filter_element = await self.find_filter_section()
            export_button = await self.find_export_button(filter_element)
            dropdown_element = await self.show_and_find_dropdown(export_button)
            dropdown_item = await self.find_dropdown_item(dropdown_element)

            # 点击dropdown-item
            if dropdown_item:
                await dropdown_item.click()
                self.logger.info("已点击'基础信息导出'dropdown-item")

            # 处理导出modal
            await self.handle_export_modal()

            # 使用任务中心工具等待导出完成
            self.logger.info("等待任务中心处理导出...")
            download_path = await wait_for_export_task(
                page=self.page,
                filename="商品档案基础信息",  # 可选的自定义文件名
                timeout=300,  # 等待5分钟
                use_task_center=True,  # 使用任务中心模式（适用于大文件导出）
            )

            self.logger.info(f"商品档案导出完成，文件保存路径: {download_path}")
            return download_path

        except Exception as e:
            self.logger.error(f"商品档案导出失败: {str(e)}")
            await self.take_screenshot("goods_archive_error.png")
            raise
