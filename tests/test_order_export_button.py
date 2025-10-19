"""
订单导出按钮测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.order import OrderCrawler
from app.utils.logger import get_logger


async def test_export_button_only():
    """
    只测试导出按钮点击功能
    """
    logger = get_logger("test_export_button")

    try:
        logger.info("=" * 50)
        logger.info("开始测试订单导出按钮")
        logger.info("=" * 50)

        # 创建爬虫实例
        crawler = OrderCrawler()

        # 运行到字段选择完成
        async with crawler.browser_session():
            logger.info("登录并导航到订单页面...")

            # 登录检查
            if not await crawler.check_login_status():
                await crawler.login()

            # 导航到订单页面
            await crawler.navigate_to(crawler.target_url)

            # 展开高级筛选
            logger.info("展开高级筛选...")
            base_filter = await crawler.page.wait_for_selector(".base-filter", timeout=10000)
            filter_advance = await base_filter.query_selector(".filter__advance-trigger")

            if filter_advance:
                text_content = await filter_advance.text_content()
                if text_content and text_content.strip() == "高级筛选":
                    await filter_advance.click()
                    await asyncio.sleep(0.5)
                    logger.info("已展开高级筛选")

            # 填写发货日期
            logger.info("填写发货日期...")
            filter_cols = await crawler.page.query_selector_all(".filter__col")
            for col in filter_cols:
                input_element = await col.query_selector("input")
                if input_element:
                    input_placeholder = await input_element.get_attribute("placeholder")
                    if input_placeholder and "发货日期" in input_placeholder:
                        date_text = "2025-10-01 - 2025-10-15"
                        await input_element.fill(date_text)
                        await input_element.press("Enter")
                        logger.info(f"已填写发货日期: {date_text}")
                        break

            # 点击查询
            logger.info("点击查询按钮...")
            filter_btns = await crawler.page.wait_for_selector(".filter__button-wrap", timeout=10000)
            search_buttons = await filter_btns.query_selector_all("button")
            for btn in search_buttons:
                btn_text = await btn.text_content()
                if btn_text and btn_text.strip() == "查询":
                    await btn.click()
                    logger.info("已点击查询按钮")
                    break

            await asyncio.sleep(1)

            # 打开导出modal
            logger.info("打开导出字段modal...")
            filter_btns = await crawler.page.query_selector(".filter__button-wrap")
            export_box = await filter_btns.query_selector(".export-box")
            await export_box.hover()
            await asyncio.sleep(0.3)

            dropdown_items = await export_box.query_selector_all(".ivu-dropdown-item")
            for item in dropdown_items:
                item_text = await item.text_content()
                if item_text and item_text.strip() == "订单明细":
                    await item.click()
                    logger.info("已点击订单明细按钮")
                    break

            await asyncio.sleep(0.5)

            # 选择字段（简化版，只选择前几个）
            logger.info("选择导出字段...")
            modals = await crawler.page.query_selector_all(".ivu-modal")
            visible_modal = None
            for modal in modals:
                if await modal.is_visible():
                    visible_modal = modal
                    break

            if visible_modal:
                checkbox_group = await visible_modal.query_selector(".ivu-checkbox-group")
                if checkbox_group:
                    labels = await checkbox_group.query_selector_all("label.ivu-checkbox-group-item")
                    # 只选择前6个字段
                    for i, label in enumerate(labels[:6]):
                        checkbox_input = await label.query_selector("input[type='checkbox']")
                        if checkbox_input and not await checkbox_input.is_checked():
                            await label.click()
                    logger.info(f"已选择6个导出字段")

            # 测试导出按钮
            logger.info("开始测试导出按钮...")

            # 找到可见的modal
            modals = await crawler.page.query_selector_all(".ivu-modal")
            visible_modal = None
            for modal in modals:
                if await modal.is_visible():
                    visible_modal = modal
                    logger.info("找到可见的modal")
                    break

            if visible_modal:
                modal = visible_modal

                # 在modal中找到footer
                modal_footer = await modal.query_selector(".ivu-modal-footer")
                if modal_footer:
                    logger.info("找到modal footer")

                    # 在footer中找到确认导出按钮
                    export_button = await modal_footer.query_selector("button:has-text('确认导出')")
                    if export_button:
                        logger.info("找到确认导出按钮")
                    else:
                        logger.warning("modal footer中找不到确认导出按钮，尝试查找确定按钮")
                        export_button = await modal_footer.query_selector("button:has-text('确定')")
                        if export_button:
                            logger.info("找到确定按钮")
                else:
                    logger.error("modal中找不到footer")

                # 如果没找到按钮，回退到遍历方式
                if not export_button:
                    logger.warning("使用回退方式查找按钮")
                    all_buttons = await modal.query_selector_all("button")
                    for btn in all_buttons:
                        btn_text = await btn.text_content()
                        if btn_text and btn_text.strip() in ["确认导出", "确定"]:
                            export_button = btn
                            logger.info(f"通过遍历找到按钮: '{btn_text}'")
                            break

                if export_button:
                    logger.info("开始点击导出按钮...")

                    # 检查按钮状态
                    is_visible = await export_button.is_visible()
                    is_enabled = await export_button.is_enabled()
                    logger.info(f"按钮状态 - 可见: {is_visible}, 可用: {is_enabled}")

                    # 尝试点击
                    try:
                        await export_button.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await export_button.click()
                        logger.info("✅ 成功点击导出按钮")
                    except Exception as e:
                        logger.warning(f"常规点击失败: {str(e)}")
                        # 尝试强制点击
                        await export_button.evaluate("(element) => element.click()")
                        logger.info("✅ 强制点击导出按钮成功")

                    # 等待任务中心
                    logger.info("等待任务中心处理...")
                    await asyncio.sleep(3)

                    return True
                else:
                    logger.error("找不到导出按钮")
                    # 调试：打印所有按钮
                    all_buttons = await modal.query_selector_all("button")
                    logger.error("所有按钮:")
                    for i, btn in enumerate(all_buttons):
                        btn_text = await btn.text_content()
                        btn_class = await btn.get_attribute("class")
                        logger.error(f"  按钮{i+1}: 文本='{btn_text}', class='{btn_class}'")
            else:
                logger.error("找不到modal")

        return False

    except Exception as e:
        logger.error(f"导出按钮测试失败: {str(e)}")
        return False


async def main():
    """主函数"""
    logger = get_logger("test_main")

    success = await test_export_button_only()

    if success:
        logger.info("✅ 导出按钮测试通过")
    else:
        logger.error("❌ 导出按钮测试失败")


if __name__ == "__main__":
    asyncio.run(main())