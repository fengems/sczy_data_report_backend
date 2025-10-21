"""
财务毛利爬虫模块
用于爬取ERP系统中的财务毛利数据
"""

import asyncio
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import Locator, Page

from app.crawlers.base import BaseCrawler
from app.crawlers.utils.task_center import TaskCenterUtils
from app.utils.logger import get_logger


class FinanceProfitCrawler(BaseCrawler):
    """财务毛利爬虫类"""

    def __init__(self):
        super().__init__("finance_profit")
        self.task_center: Optional[TaskCenterUtils] = None
        self.target_url = "/cc_sssp/superAdmin/viewCenter/v1/reports/profit/finance"

        # 默认导出字段
        self.default_export_fields = [
            "商品名称",
            "商品编码",
            "商品ID",
            "一级分类",
            "二级分类",
            "下单单位",
            "下单数量",
            "发货单位",
            "发货数量",
            "实际销售金额",
            "实际成本",
            "销售毛利",
            "销售毛利率",
        ]

    async def login(self) -> bool:
        """登录ERP系统"""
        try:
            self.logger.info("开始登录ERP系统...")

            # 导入并使用现有的ERP认证模块
            from app.crawlers.auth import ERPAuthCrawler

            auth_crawler = ERPAuthCrawler()
            auth_crawler.browser = self.browser
            auth_crawler.context = self.context
            auth_crawler.page = self.page

            # 执行登录
            result = await auth_crawler.login()

            if result:
                # 初始化任务中心工具
                self.task_center = TaskCenterUtils(self.page)
                self.logger.info("ERP系统登录成功，任务中心工具已初始化")
                return True
            else:
                self.logger.error("ERP系统登录失败")
                return False

        except Exception as e:
            self.logger.error(f"登录过程中发生错误: {str(e)}")
            return False

    async def crawl_data(self, params: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """
        爬取财务毛利数据的主要流程

        Args:
            params: 包含爬取参数的字典
                - date_range: 日期范围 ["2025-10-01", "2025-10-07"]
                - export_fields: 导出字段列表（可选）

        Returns:
            str: 下载文件的完整路径
        """
        try:
            self.logger.info("开始爬取财务毛利数据...")

            # 检查page是否已初始化
            if self.page is None:
                raise RuntimeError("浏览器页面未初始化，请先调用login()方法")

            # 验证参数
            date_range = params.get("date_range")
            if (
                not date_range
                or not isinstance(date_range, list)
                or len(date_range) != 2
            ):
                raise ValueError("日期范围参数无效，需要包含两个日期的数组")

            export_fields = params.get("export_fields", self.default_export_fields)

            # 步骤1: 导航到财务毛利页面
            await self.navigate_to(self.target_url)
            self.logger.info("已导航到财务毛利页面")

            # 步骤2: 找到filter栏
            s_filter = await self._find_filter_section()
            if not s_filter:
                raise RuntimeError("未找到筛选栏")

            # 步骤3: 找到展开按钮并展开筛选栏
            await self._expand_advanced_filter(s_filter)

            # 步骤4: 填充筛选日期
            await self._fill_date_filter(s_filter, date_range)

            # 步骤5: 找到导出按钮并hover
            await self._hover_export_button(s_filter)

            # 步骤6: 点击导出汇总数据
            await self._click_export_summary_data()

            # 步骤7: 找到modal弹窗
            modal = await self._find_export_modal()
            if modal is None:
                raise RuntimeError("未找到导出设置弹窗")

            # 步骤8: 选择导出字段
            await self._select_export_fields(modal, export_fields)

            # 步骤9: 点击确认导出按钮
            await self._click_confirm_export(modal)

            # 步骤10: 使用任务中心下载文件
            if not self.task_center:
                raise RuntimeError("任务中心工具未初始化")

            file_path = await self.task_center.wait_for_export_task("财务毛利")

            self.logger.info(f"财务毛利数据爬取完成，文件路径: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"爬取财务毛利数据失败: {str(e)}")
            raise

    async def _find_filter_section(self) -> Locator:
        """找到filter栏"""
        try:
            self.logger.info("查找筛选栏...")

            # 使用Locator API查找筛选栏，使用first()选择第一个可见的筛选栏
            assert self.page is not None, "浏览器页面未初始化"
            s_filter = self.page.locator(".s-filter").first
            await s_filter.wait_for(state="visible", timeout=10000)

            self.logger.info("找到筛选栏")
            return s_filter

        except Exception as e:
            self.logger.error(f"查找筛选栏失败: {str(e)}")
            raise

    async def _expand_advanced_filter(self, s_filter: Locator) -> None:
        """找到展开按钮并展开筛选栏"""
        try:
            self.logger.info("检查高级筛选状态...")

            # 在sFilter中查找展开按钮
            s_filter_toggle = s_filter.locator(".s-filter__advance-toggle")

            if await s_filter_toggle.count() == 0:
                self.logger.warning("未找到高级筛选按钮，可能已经展开")
                return

            # 获取按钮文本
            toggle_text = await s_filter_toggle.first.text_content()
            if toggle_text:
                toggle_text = toggle_text.strip()

                if toggle_text == "高级筛选":
                    self.logger.info("点击展开高级筛选...")
                    await s_filter_toggle.first.click()
                    # 等待动画完成
                    await asyncio.sleep(0.5)
                    self.logger.info("高级筛选已展开")
                elif toggle_text == "收起高级筛选":
                    self.logger.info("高级筛选已展开")
                else:
                    self.logger.warning(f"未知的按钮文本: {toggle_text}")

        except Exception as e:
            self.logger.error(f"展开高级筛选失败: {str(e)}")
            raise

    async def _fill_date_filter(self, s_filter: Locator, date_range: List[str]) -> None:
        """填充筛选日期"""
        try:
            self.logger.info(f"填充日期范围: {date_range}")

            # 在sFilter中查找日期选择器
            date_picker = s_filter.locator(".ivu-date-picker")
            await date_picker.wait_for(state="visible", timeout=10000)

            # 在datePicker中查找输入框
            date_input = date_picker.locator("input.ivu-input")
            await date_input.wait_for(state="visible", timeout=5000)

            # 构造日期范围文本
            date_range_text = f"{date_range[0]} - {date_range[1]}"
            self.logger.info(f"日期范围文本: {date_range_text}")

            # 填充日期输入框
            await date_input.fill(date_range_text)

            # 触发回车事件，让ERP表单更新
            await date_input.press("Enter")
            await asyncio.sleep(0.5)  # 等待表单更新

            self.logger.info("日期范围填充完成")

        except Exception as e:
            self.logger.error(f"填充日期筛选失败: {str(e)}")
            raise

    async def _hover_export_button(self, s_filter: Locator) -> None:
        """找到导出按钮并hover"""
        try:
            self.logger.info("查找导出按钮...")

            # 在sFilter中查找下拉菜单
            dropdown = s_filter.locator(".ivu-dropdown").first

            # 在下拉菜单中查找按钮
            export_button = dropdown.locator(".s-button")

            # 检查按钮是否存在
            if await export_button.count() == 0:
                raise RuntimeError("未找到导出按钮")

            # 使用JavaScript强制显示按钮并触发hover事件
            await export_button.evaluate("""
                (element) => {
                    element.style.visibility = 'visible';
                    element.style.opacity = '1';
                    element.style.pointerEvents = 'auto';
                    element.style.zIndex = '9999';
                    element.dispatchEvent(new MouseEvent('mouseenter', {
                        bubbles: true,
                        cancelable: true
                    }));
                }
            """)

            # 等待下拉菜单显示
            await asyncio.sleep(2)

            self.logger.info("已处理导出按钮")

        except Exception as e:
            self.logger.error(f"处理导出按钮失败: {str(e)}")
            raise

    async def _click_export_summary_data(self) -> None:
        """点击导出汇总数据"""
        try:
            self.logger.info("查找并点击'汇总数据'选项...")

            # 查找所有包含"汇总数据"文本的元素
            assert self.page is not None, "浏览器页面未初始化"
            summary_data_items = self.page.locator(
                ".ivu-dropdown-item", has_text="汇总数据"
            )

            # 检查是否有这样的元素
            if await summary_data_items.count() > 0:
                # 直接使用JavaScript强制显示并点击第一个汇总数据选项
                await summary_data_items.first.evaluate("""
                    (element) => {
                        // 强制显示元素
                        element.style.display = 'block';
                        element.style.visibility = 'visible';
                        element.style.opacity = '1';
                        element.style.pointerEvents = 'auto';
                        element.style.zIndex = '9999';

                        // 直接触发点击事件
                        element.click();
                        return element;
                    }
                """)
                self.logger.info("已通过JavaScript强制点击'汇总数据'选项")
            else:
                raise RuntimeError("未找到'汇总数据'选项")

            # 等待弹窗出现
            await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"点击导出汇总数据失败: {str(e)}")
            raise

    async def _find_export_modal(self) -> Locator:
        """找到导出modal弹窗"""
        try:
            self.logger.info("查找导出设置弹窗...")

            assert self.page is not None, "浏览器页面未初始化"

            # 等待modal出现
            await asyncio.sleep(2)

            # 直接使用 .ivu-modal 选择器
            modals = self.page.locator(".ivu-modal")

            # 获取所有可见的modal
            visible_modals = []
            count = await modals.count()

            for i in range(count):
                modal = modals.nth(i)
                if await modal.is_visible():
                    visible_modals.append(modal)

            if not visible_modals:
                self.logger.error("未找到任何可见的 .ivu-modal 元素")
                await self._debug_modal_search()
                raise RuntimeError("未找到任何导出设置弹窗")

            # 如果有多个可见modal，优先选择包含导出相关文本的
            export_modal = None
            fallback_modal = visible_modals[0]  # 默认使用第一个

            for modal in visible_modals:
                try:
                    text = await modal.text_content()
                    if text and any(
                        keyword in text for keyword in ["导出", "字段", "选择"]
                    ):
                        export_modal = modal
                        self.logger.info(f"找到导出相关modal: {text[:50]}...")
                        break
                except Exception:
                    # 获取文本失败时继续检查下一个
                    continue

            result_modal = export_modal or fallback_modal

            # 截图保存找到的modal状态
            try:
                await self.take_screenshot("modal_found_debug.png")
                self.logger.debug("已保存modal截图")
            except Exception as e:
                self.logger.debug(f"截图失败: {e}")

            self.logger.info("成功找到导出设置弹窗")
            return result_modal

        except Exception as e:
            self.logger.error(f"查找导出弹窗失败: {str(e)}")
            await self._debug_modal_search()
            raise

    async def _debug_modal_search(self) -> None:
        """调试modal搜索过程"""
        try:
            assert self.page is not None, "浏览器页面未初始化"

            # 截图当前页面状态
            await self.take_screenshot("modal_search_debug.png")

            # 查找所有可能的对话框元素
            all_elements = await self.page.evaluate("""
                () => {
                    const elements = [];
                    const selectors = ['.ivu-modal', '.modal', '[role="dialog"]', '.ivu-modal-wrap'];

                    selectors.forEach(selector => {
                        const els = document.querySelectorAll(selector);
                        els.forEach((el, index) => {
                            elements.push({
                                selector: selector,
                                index: index,
                                visible: el.offsetParent !== null,
                                text: el.innerText.substring(0, 100),
                                display: window.getComputedStyle(el).display,
                                zIndex: window.getComputedStyle(el).zIndex
                            });
                        });
                    });

                    return elements;
                }
            """)

            self.logger.info(f"页面中找到的对话框元素: {all_elements}")

        except Exception as e:
            self.logger.warning(f"调试modal搜索失败: {e}")

    async def _select_export_fields(
        self, modal: Locator, export_fields: List[str]
    ) -> None:
        """选择导出字段"""
        try:
            self.logger.info(f"选择导出字段: {export_fields}")

            # 先等待modal内容加载完成
            await asyncio.sleep(1)

            # 在modal中查找第一个checkbox组，增加超时时间
            checkbox_group = modal.locator(".ivu-checkbox-group").first

            # 检查是否存在checkbox组
            if await checkbox_group.count() == 0:
                self.logger.warning("未找到checkbox组，尝试查找其他可能的字段选择元素")
                # 尝试其他可能的selector
                alternative_checkbox = modal.locator(".ivu-checkbox-wrapper")
                if await alternative_checkbox.count() > 0:
                    self.logger.info("使用替代的checkbox selector")
                    checkbox_items = alternative_checkbox
                else:
                    raise RuntimeError("modal中未找到任何checkbox元素")
            else:
                # 等待checkbox组可见
                await checkbox_group.wait_for(state="visible", timeout=10000)
                # 查找所有checkbox选项
                checkbox_items = checkbox_group.locator("label.ivu-checkbox-group-item")

            # 遍历所有checkbox选项，根据导出字段设置选中状态
            item_count = await checkbox_items.count()
            fields_found = []

            for i in range(item_count):
                item = checkbox_items.nth(i)

                # 获取选项文本
                label_text = await item.text_content()
                if label_text:
                    label_text = label_text.strip()

                    # 查找checkbox input元素
                    checkbox_input = item.locator("input[type='checkbox']")

                    if await checkbox_input.count() > 0:
                        # 检查当前选中状态
                        is_checked = await checkbox_input.first.is_checked()
                        # 是否应该被选中
                        should_be_checked = label_text in export_fields

                        fields_found.append(label_text)

                        # 如果状态不匹配，点击切换
                        if is_checked != should_be_checked:
                            await item.click()
                            self.logger.debug(
                                f"字段 '{label_text}' 状态已切换为: {should_be_checked}"
                            )

            # 检查是否所有需要的字段都找到了
            missing_fields = set(export_fields) - set(fields_found)
            if missing_fields:
                self.logger.warning(f"以下字段未找到: {missing_fields}")

            self.logger.info(f"导出字段选择完成，找到 {len(fields_found)} 个字段")

        except Exception as e:
            self.logger.error(f"选择导出字段失败: {str(e)}")
            raise

    async def _click_confirm_export(self, modal: Locator) -> None:
        """点击确认导出按钮"""
        try:
            self.logger.info("查找并点击确认导出按钮...")

            # 在页面中查找确认导出按钮
            assert self.page is not None, "浏览器页面未初始化"
            confirm_button = modal.locator("button", has_text="确认导出")

            # 检查是否有这样的按钮
            if await confirm_button.count() > 0:
                # 直接点击第一个确认导出按钮
                await confirm_button.first.click()
                self.logger.info("已点击确认导出按钮，触发导出任务...")
            else:
                # 如果没找到确认导出按钮，尝试通过JavaScript直接触发
                self.logger.warning("未找到确认导出按钮，尝试JavaScript触发")
                assert self.page is not None, "浏览器页面未初始化"
                await self.page.evaluate("""
                    () => {
                        // 查找所有确认导出按钮
                        const buttons = document.querySelectorAll('button');
                        for (let button of buttons) {
                            if (button.textContent && button.textContent.includes('确认导出')) {
                                button.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)

        except Exception as e:
            self.logger.error(f"点击确认导出按钮失败: {str(e)}")
            raise
