"""
订单中心爬虫模块
"""
import asyncio
from typing import List, Optional, Dict, Any

from app.crawlers.base import BaseCrawler
from app.crawlers.utils.task_center import TaskCenterUtils


class OrderCrawler(BaseCrawler):
    """订单中心爬虫"""

    def __init__(self):
        super().__init__("order")
        self.task_center = None  # 将在browser_session初始化后设置
        self.target_url = "/cc_sssp/superAdmin/viewCenter/v1/order/list"

    async def login(self) -> bool:
        """
        使用现有的ERP认证模块进行登录
        """
        from app.crawlers.auth import ERPAuthCrawler

        auth_crawler = ERPAuthCrawler()
        auth_crawler.browser = self.browser
        auth_crawler.context = self.context
        auth_crawler.page = self.page
        result = await auth_crawler.login()

        # 初始化任务中心工具
        if result:
            self.task_center = TaskCenterUtils(self.page)

        return result

    def _ensure_page(self):
        """确保页面已初始化"""
        if not self.page:
            raise Exception("页面未初始化")
        return self.page

    async def crawl_data(self, params: Dict[str, Any]) -> str:
        """
        爬取订单数据

        Args:
            params: 包含爬取参数的字典
                - delivery_date_range: 发货日期时间段 ["2025-10-01", "2025-10-15"]
                - order_time_range: 下单时间时间段 ["2025-10-01 00:00", "2025-10-15 00:00"]
                - export_fields: 导出字段列表

        Returns:
            str: 下载文件路径
        """
        self.logger.info("开始爬取订单数据...")

        # 导航到订单页面
        await self.navigate_to(self.target_url)

        # 从params中提取参数
        delivery_date_range = params.get("delivery_date_range")
        order_time_range = params.get("order_time_range")
        export_fields = params.get("export_fields")

        # 1. 打开全部筛选
        await self._open_advanced_filter()

        # 2. 填写筛选条件
        await self._fill_filter_conditions(delivery_date_range, order_time_range)

        # 3. 点击查找
        await self._click_search()

        # 4. 打开导出字段modal
        await self._open_export_modal()

        # 5. 选择要导出的字段
        await self._select_export_fields(export_fields)

        # 6. 点击导出
        await self._click_export()

        # 7. 任务中心导出流程
        if not self.task_center:
            raise Exception("任务中心工具未初始化")
        file_path = await self.task_center.wait_for_export_task("订单明细")

        self.logger.info(f"订单数据导出完成，文件保存路径: {file_path}")
        return file_path

    async def _open_advanced_filter(self):
        """打开全部筛选"""
        self.logger.info("开始打开高级筛选...")

        # 找到baseFilter元素
        page = self._ensure_page()
        base_filter = page.locator(".base-filter")

        if await base_filter.count() == 0:
            raise Exception("找不到baseFilter元素")

        # 在baseFilter内部找到filterAdvanace元素
        filter_advance = base_filter.locator(".filter__advance-trigger")

        if await filter_advance.count() > 0:
            # 获取第一个元素的文本
            text_content = await filter_advance.first.text_content()

            if text_content and text_content.strip() == "高级筛选":
                # 需要点击展开
                self.logger.info("点击展开高级筛选...")
                await filter_advance.first.click()
                # 等待展开动画完成
                await asyncio.sleep(0.5)
            else:
                self.logger.info("高级筛选已展开")
        else:
            raise Exception("找不到高级筛选按钮")

    async def _fill_filter_conditions(
        self,
        delivery_date_range: Optional[List[str]] = None,
        order_time_range: Optional[List[str]] = None
    ):
        """填写筛选条件"""
        self.logger.info("开始填写筛选条件...")

        # 获取所有筛选项
        page = self._ensure_page()
        filter_cols = page.locator(".filter__col")

        if delivery_date_range:
            # 填写发货日期
            await self._fill_date_filter(filter_cols, "发货日期", delivery_date_range, " - ")
        elif order_time_range:
            # 填写下单时间，并清空发货日期
            await self._fill_date_filter(filter_cols, "发货日期", [], " - ", clear=True)
            await self._fill_date_filter(filter_cols, "下单时间", order_time_range, "~")
        else:
            self.logger.warning("既没有传发货日期也没有传下单时间")

    async def _fill_date_filter(
        self,
        filter_cols,
        label_name: str,
        date_range: List[str],
        separator: str,
        clear: bool = False
    ):
        """填写日期筛选条件"""
        target_filter_col = None

        # 智能查找日期筛选项
        # 发货日期和下单时间通常会有特定的placeholder或类型
        date_keywords = {
            "发货日期": ["发货", "delivery", "日期"],
            "下单时间": ["下单", "订单", "时间", "order"]
        }

        for col in await filter_cols.all():
            # 查找所有input元素
            input_elements = col.locator("input")
            if await input_elements.count() > 0:
                # 遍历所有input元素，找到我们需要的那一个
                for i in range(await input_elements.count()):
                    input_element = input_elements.nth(i)
                    input_placeholder = await input_element.get_attribute("placeholder")
                    input_type = await input_element.get_attribute("type")

                    # 检查placeholder或类型是否匹配
                    for keyword in date_keywords.get(label_name, []):
                        if (input_placeholder and keyword in input_placeholder) or \
                           (input_type and "date" in input_type.lower()):
                            target_filter_col = col
                            self.logger.info(f"通过input属性找到{label_name}筛选项，placeholder: {input_placeholder}, type: {input_type}")
                            break

                    if target_filter_col:
                        break

            if target_filter_col:
                break

        # 如果通过input属性没找到，尝试文本匹配
        if not target_filter_col:
            for col in await filter_cols.all():
                # 尝试多种方式获取标签文本
                elements_to_check = col.locator("label, span, div")

                for element in await elements_to_check.all():
                    text_content = await element.text_content()
                    if text_content:
                        text_content = text_content.strip()
                        # 精确匹配
                        if text_content == label_name:
                            target_filter_col = col
                            self.logger.info(f"通过精确文本匹配找到{label_name}筛选项: {text_content}")
                            break
                        # 模糊匹配
                        elif any(keyword in text_content for keyword in date_keywords.get(label_name, [])):
                            target_filter_col = col
                            self.logger.info(f"通过模糊文本匹配找到{label_name}筛选项: {text_content}")
                            break

                if target_filter_col:
                    break

        if not target_filter_col:
            raise Exception(f"找不到{label_name}筛选项")

        # 找到input元素（之前已经找到了正确的input_element）
        # 重新确认input元素的存在和获取正确的input
        input_elements = target_filter_col.locator("input")
        if await input_elements.count() == 0:
            raise Exception(f"在{label_name}筛选项中找不到input元素")

        # 找到第一个符合日期筛选条件的input（不是隐藏的那个）
        input_element = None
        for i in range(await input_elements.count()):
            candidate = input_elements.nth(i)
            placeholder = await candidate.get_attribute("placeholder")
            input_type = await candidate.get_attribute("type")

            # 检查是否是我们要的日期输入框
            for keyword in date_keywords.get(label_name, []):
                if (placeholder and keyword in placeholder) or \
                   (input_type and "date" in input_type.lower()):
                    input_element = candidate
                    break

            if input_element:
                break

        if not input_element:
            raise Exception(f"在{label_name}筛选项中找不到合适的input元素")

        if clear:
            # 清空输入
            await input_element.fill("")
            await input_element.press("Backspace")
            await asyncio.sleep(0.1)  # 等待清空完成
            self.logger.info(f"已清空{label_name}筛选项")
        elif date_range and len(date_range) == 2:
            # 填写日期范围
            date_text = f"{date_range[0]}{separator}{date_range[1]}"
            await input_element.fill(date_text)
            self.logger.info(f"已填写{label_name}: {date_text}")

            # 触发回车事件
            await input_element.press("Enter")
            await asyncio.sleep(0.2)  # 等待表单更新
        else:
            self.logger.warning(f"{label_name}参数格式不正确")

    async def _click_search(self):
        """点击查找按钮"""
        self.logger.info("点击查询按钮...")

        # 获取筛选项按钮区域
        page = self._ensure_page()
        filter_btns = page.locator(".filter__button-wrap")

        if await filter_btns.count() == 0:
            raise Exception("找不到筛选项按钮区域")

        # 找到查询按钮
        search_buttons = filter_btns.locator("button")
        search_button = None

        for btn in await search_buttons.all():
            btn_text = await btn.text_content()
            if btn_text and btn_text.strip() == "查询":
                search_button = btn
                break

        if not search_button:
            raise Exception("找不到查询按钮")

        await search_button.click()
        self.logger.info("已点击查询按钮，等待表格刷新...")
        await asyncio.sleep(1)  # 等待表格接口请求完成

    async def _open_export_modal(self):
        """打开导出字段modal"""
        self.logger.info("开始打开导出字段modal...")

        # 获取筛选项按钮区域
        page = self._ensure_page()
        filter_btns = page.locator(".filter__button-wrap")
        if await filter_btns.count() == 0:
            raise Exception("找不到筛选项按钮区域")

        # 找到export-box
        export_box = filter_btns.locator(".export-box")
        if await export_box.count() == 0:
            raise Exception("找不到导出框")

        # hover到export-box
        await export_box.hover()
        await asyncio.sleep(0.3)  # 等待dropdown展开

        # 找到"订单明细"按钮
        order_detail_btn = None
        dropdown_items = export_box.locator(".ivu-dropdown-item")

        for item in await dropdown_items.all():
            item_text = await item.text_content()
            if item_text and item_text.strip() == "订单明细":
                order_detail_btn = item
                break

        if not order_detail_btn:
            raise Exception("找不到订单明细按钮")

        await order_detail_btn.click()
        self.logger.info("已点击订单明细按钮，等待modal打开...")
        await asyncio.sleep(0.5)  # 等待modal打开

    async def _select_export_fields(self, export_fields: Optional[List[str]] = None):
        """选择要导出的字段"""
        self.logger.info("开始选择导出字段...")

        # 默认导出字段
        default_fields = [
            '订单号', '客户名称',
            '订单时间', '发货时间',
            '线路名称', '业务员',
            '一级分类', '二级分类',
            '商品名称', '发货数量',
            '发货单位', '实际金额',
            '客户类型', '区域名称',
            '订单标识', '客户标签'
        ]

        # 使用传入的字段或默认字段
        fields_to_export = export_fields if export_fields else default_fields

        # 找到可见的modal
        page = self._ensure_page()
        modals = page.locator(".ivu-modal")
        visible_modal = None

        for modal in await modals.all():
            if await modal.is_visible():
                visible_modal = modal
                self.logger.info("找到可见的modal")
                break

        if not visible_modal:
            raise Exception("找不到可见的modal")

        modal = visible_modal

        # 找到checkbox group
        checkbox_group = modal.locator(".ivu-checkbox-group")
        if await checkbox_group.count() == 0:
            raise Exception("modal中找不到checkbox group")

        # 找到所有labels
        labels = checkbox_group.locator("label.ivu-checkbox-group-item")

        # 遍历所有labels，设置勾选状态
        for label in await labels.all():
            label_text = await label.text_content()
            if label_text:
                label_text = label_text.strip()

                # 找到对应的checkbox input
                checkbox_input = label.locator("input[type='checkbox']")
                if await checkbox_input.count() > 0:
                    is_checked = await checkbox_input.is_checked()
                    should_be_checked = label_text in fields_to_export

                    if is_checked != should_be_checked:
                        # 需要改变勾选状态
                        await label.click()
                        self.logger.debug(f"字段 '{label_text}' {'勾选' if should_be_checked else '取消勾选'}")

        self.logger.info(f"已选择 {len(fields_to_export)} 个导出字段")

    async def _click_export(self):
        """点击导出按钮"""
        self.logger.info("开始点击导出按钮...")

        # 找到modal - 使用之前找到的可见modal逻辑
        page = self._ensure_page()
        modals = page.locator(".ivu-modal")
        visible_modal = None

        for modal in await modals.all():
            if await modal.is_visible():
                visible_modal = modal
                self.logger.info("找到可见的modal")
                break

        if not visible_modal:
            raise Exception("找不到可见的modal")

        modal = visible_modal

        # 在modal中找到footer
        modal_footer = modal.locator(".ivu-modal-footer")
        if await modal_footer.count() == 0:
            raise Exception("modal中找不到footer")

        # 在footer中找到确认导出按钮
        export_button = modal_footer.locator("button:has-text('确认导出')")
        if await export_button.count() == 0:
            raise Exception("modal footer中找不到确认导出按钮")

        # 检查按钮是否可见
        is_visible = await export_button.is_visible()
        if not is_visible:
            self.logger.warning("确认导出按钮不可见，尝试点击")

        # 点击按钮
        try:
            await export_button.click()
            self.logger.info("已点击确认导出按钮，触发导出任务...")
        except Exception as e:
            self.logger.warning(f"常规点击失败，尝试强制点击: {str(e)}")
            # 强制点击
            await export_button.evaluate("(element) => element.click()")
            self.logger.info("已强制点击确认导出按钮")

        # 等待任务中心处理
        await asyncio.sleep(1)