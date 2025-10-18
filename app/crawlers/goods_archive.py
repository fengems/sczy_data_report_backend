"""
商品档案爬虫模块
用于从ERP系统导出商品档案基础信息
"""
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from app.crawlers.base import BaseCrawler
from app.config.settings import settings
from app.utils.logger import get_logger
from app.crawlers.utils import wait_for_export_task


class GoodsArchiveCrawler(BaseCrawler):
    """商品档案爬虫"""

    def __init__(self):
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

    async def find_filter_section(self) -> Optional[Any]:
        """
        步骤1: 找到filter部分
        寻找页面上可见的 ".filter__button-wrap" 或者 ".filter__operation__btn-wrap"
        """
        try:
            self.logger.info("开始定位filter部分...")

            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # 额外等待确保JS渲染完成

            # 尝试多个可能的filter选择器
            filter_selectors = [
                ".filter__button-wrap",
                ".filter__operation__btn-wrap",
                ".filter-button-wrap",
                ".filter-operation-btn-wrap",
                "[class*='filter'][class*='button']",
                "[class*='filter'][class*='operation']"
            ]

            filter_element = None
            found_selector = None

            for selector in filter_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # 检查元素是否可见
                        is_visible = await element.is_visible()
                        if is_visible:
                            filter_element = element
                            found_selector = selector
                            self.logger.info(f"找到filter部分，选择器: {selector}")
                            break
                except:
                    continue

            if not filter_element:
                self.logger.warning("未找到filter部分，尝试通过按钮文本定位...")
                # 备用方案：通过包含"导出"文本的按钮来定位filter区域
                export_buttons = await self.page.query_selector_all("button")
                for button in export_buttons:
                    try:
                        text = await button.text_content()
                        if text and "导出" in text.strip():
                            # 查找按钮的父级容器，可能是filter区域
                            parent = await button.evaluate("""(element) => {
                                let parent = element.parentElement;
                                while (parent && parent !== document.body) {
                                    if (parent.className && (
                                        parent.className.includes('filter') ||
                                        parent.className.includes('operation') ||
                                        parent.className.includes('button-wrap')
                                    )) {
                                        return parent;
                                    }
                                    parent = parent.parentElement;
                                }
                                return null;
                            }""")
                            if parent:
                                filter_element = button
                                found_selector = "parent_of_export_button"
                                self.logger.info("通过导出按钮定位到filter区域")
                                break
                    except:
                        continue

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
                "button[title*='导出']"
            ]

            export_button = None

            for selector in export_selectors:
                try:
                    # 如果在filter区域内查找
                    if filter_element and hasattr(filter_element, 'query_selector'):
                        button = await filter_element.query_selector(selector)
                    else:
                        button = await self.page.wait_for_selector(selector, timeout=5000)

                    if button:
                        # 验证按钮文本
                        text = await button.text_content()
                        if text and text.strip().replace(" ", "") == "导出":
                            is_visible = await button.is_visible()
                            if is_visible:
                                export_button = button
                                self.logger.info(f"找到导出按钮，选择器: {selector}")
                                break
                except:
                    continue

            # 备用方案：查找所有按钮，筛选文本内容
            if not export_button:
                self.logger.info("使用备用方案定位导出按钮...")
                all_buttons = await self.page.query_selector_all("button")
                for button in all_buttons:
                    try:
                        text = await button.text_content()
                        if text and text.strip().replace(" ", "") == "导出":
                            is_visible = await button.is_visible()
                            if is_visible:
                                export_button = button
                                self.logger.info("通过文本匹配找到导出按钮")
                                break
                    except:
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

            # 给dropdown更多时间出现和渲染
            await asyncio.sleep(2)  # 增加等待时间

            # 等待页面稳定
            await self.page.wait_for_load_state("networkidle")

            # 查找dropdown元素 - 增加更多选择器和更长的等待时间
            dropdown_selectors = [
                ".ivu-select-dropdown",
                ".ivu-dropdown",
                ".ivu-dropdown-menu",
                ".ivu-select-dropdown-list",
                "[class*='dropdown']",
                "[class*='select-dropdown']",
                "[class*='dropdown-menu']",
                "[class*='dropdown-list']",
                "ul[class*='dropdown']",  # 可能是ul列表
                "div[class*='dropdown']:visible",
                ".ivu-dropdown-drop"  # iView特有的dropdown容器
            ]

            dropdown_element = None

            for selector in dropdown_selectors:
                try:
                    # 使用更长的等待时间
                    element = await self.page.wait_for_selector(selector, timeout=10000)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            dropdown_element = element
                            self.logger.info(f"找到dropdown元素，选择器: {selector}")
                            break
                except:
                    continue

            if not dropdown_element:
                # 备用方案：查找所有可能的新出现的下拉菜单
                self.logger.info("使用备用方案查找dropdown...")
                all_dropdowns = await self.page.query_selector_all(
                    ".ivu-select-dropdown, .ivu-dropdown, .ivu-dropdown-menu, .ivu-select-dropdown-list, [class*='dropdown'], [class*='dropdown-menu'], ul[class*='dropdown']"
                )
                self.logger.info(f"找到 {len(all_dropdowns)} 个潜在dropdown元素")

                for i, dropdown in enumerate(all_dropdowns):
                    try:
                        is_visible = await dropdown.is_visible()
                        if is_visible:
                            # 检查dropdown的位置，确保它在导出按钮附近
                            button_box = await export_button.bounding_box()
                            dropdown_box = await dropdown.bounding_box()

                            if button_box and dropdown_box:
                                # 检查dropdown是否在按钮下方附近
                                if abs(dropdown_box['x'] - button_box['x']) < 200 and dropdown_box['y'] > button_box['y']:
                                    dropdown_element = dropdown
                                    self.logger.info(f"通过位置检查找到dropdown元素，位置: {dropdown_box}")
                                    break
                            else:
                                # 如果无法获取位置，使用第一个可见的
                                dropdown_element = dropdown
                                self.logger.info("使用第一个可见的dropdown元素")
                                break
                    except:
                        continue

            if not dropdown_element:
                # 最后的备用方案：直接查找所有包含"基础信息导出"文本的元素
                self.logger.info("使用最终备用方案：直接查找包含'基础信息导出'的元素...")
                try:
                    target_element = await self.page.wait_for_selector(
                        "text='基础信息导出'",
                        timeout=5000
                    )
                    if target_element:
                        # 找到目标元素的父级dropdown容器
                        dropdown_parent = await target_element.evaluate("""(element) => {
                            let parent = element.parentElement;
                            while (parent && parent !== document.body) {
                                if (parent.className && (
                                    parent.className.includes('dropdown') ||
                                    parent.className.includes('select') ||
                                    parent.className.includes('menu') ||
                                    parent.tagName === 'UL'
                                )) {
                                    return parent;
                                }
                                parent = parent.parentElement;
                            }
                            return null;
                        }""")
                        if dropdown_parent:
                            dropdown_element = dropdown_parent
                            self.logger.info("通过目标元素反向定位到dropdown容器")
                except:
                    pass

            if not dropdown_element:
                raise RuntimeError("无法找到dropdown元素")

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

            # 直接查找包含目标文本的元素作为主要方案
            try:
                target_element = await self.page.wait_for_selector(
                    "text='基础信息导出'",
                    timeout=10000
                )
                if target_element:
                    # 验证元素是否可见和可点击
                    is_visible = await target_element.is_visible()
                    if is_visible:
                        self.logger.info("直接找到'基础信息导出'元素")
                        return target_element
            except:
                self.logger.info("直接查找失败，尝试在dropdown区域内查找...")

            # 如果dropdown_element存在且可查找，在其中搜索
            if dropdown_element and hasattr(dropdown_element, 'query_selector'):
                # 在dropdown中查找目标项
                item_selectors = [
                    "li.ivu-dropdown-item:has-text('基础信息导出')",
                    ".ivu-dropdown-item:has-text('基础信息导出')",
                    "li:has-text('基础信息导出')",
                    "[class*='dropdown-item']:has-text('基础信息导出')",
                    "*:has-text('基础信息导出')"  # 通用选择器
                ]

                dropdown_item = None

                for selector in item_selectors:
                    try:
                        item = await dropdown_element.query_selector(selector)
                        if item:
                            # 验证文本内容
                            text = await item.text_content()
                            if text and "基础信息导出" in text.strip():
                                is_visible = await item.is_visible()
                                if is_visible:
                                    dropdown_item = item
                                    self.logger.info(f"在dropdown中找到目标项，选择器: {selector}")
                                    break
                    except:
                        continue

                if dropdown_item:
                    return dropdown_item

            # 备用方案：全局查找所有可能的dropdown-item
            self.logger.info("使用备用方案：全局查找dropdown-item...")
            all_selectors = [
                "li.ivu-dropdown-item",
                ".ivu-dropdown-item",
                "[class*='dropdown-item']",
                "li",
                "div[class*='item']",
                "*[role='menuitem']"  # 可能的菜单项角色
            ]

            for selector in all_selectors:
                try:
                    all_items = await self.page.query_selector_all(selector)
                    self.logger.info(f"使用选择器 {selector} 找到 {len(all_items)} 个元素")

                    for item in all_items:
                        try:
                            text = await item.text_content()
                            if text and "基础信息导出" in text.strip():
                                is_visible = await item.is_visible()
                                if is_visible:
                                    # 检查是否可点击
                                    is_enabled = await item.is_enabled()
                                    if is_enabled:
                                        dropdown_item = item
                                        self.logger.info(f"通过选择器 {selector} 找到目标元素: '{text.strip()}'")
                                        return dropdown_item
                        except:
                            continue
                except:
                    continue

            # 最终备用方案：使用JavaScript进行更精确的搜索
            self.logger.info("使用JavaScript进行最终搜索...")
            try:
                js_result = await self.page.evaluate("""
                    () => {
                        // 查找所有包含目标文本的元素
                        const targetText = '基础信息导出';
                        const allElements = document.getElementsByTagName('*');
                        const candidates = [];

                        for (let element of allElements) {
                            if (element.textContent && element.textContent.includes(targetText)) {
                                // 检查是否是可见的可点击元素
                                const style = window.getComputedStyle(element);
                                const rect = element.getBoundingClientRect();

                                if (style.display !== 'none' &&
                                    style.visibility !== 'hidden' &&
                                    rect.width > 0 && rect.height > 0) {

                                    // 检查是否是菜单项或链接类型
                                    const tagName = element.tagName.toLowerCase();
                                    const className = element.className || '';

                                    if (tagName === 'li' || tagName === 'a' || tagName === 'button' ||
                                        className.includes('item') || className.includes('dropdown') ||
                                        element.onclick || element.getAttribute('onclick')) {

                                        // 安全地获取元素索引
                                        let index = -1;
                                        if (element.parentElement && element.parentElement.children) {
                                            index = Array.from(element.parentElement.children).indexOf(element);
                                        }

                                        candidates.push({
                                            element: element,
                                            text: element.textContent.trim(),
                                            tagName: tagName,
                                            className: className,
                                            index: index
                                        });
                                    }
                                }
                            }
                        }

                        // 返回最佳候选者的信息
                        if (candidates.length > 0) {
                            const best = candidates[0];
                            return {
                                found: true,
                                text: best.text,
                                tagName: best.tagName,
                                className: best.className,
                                index: best.index
                            };
                        }

                        return { found: false };
                    }
                """)

                if js_result and js_result.get('found'):
                    self.logger.info(f"JavaScript找到目标元素: {js_result}")
                    # 直接使用最简单的文本定位
                    element = await self.page.wait_for_selector("text='基础信息导出'", timeout=5000)
                    if element:
                        return element
            except Exception as e:
                self.logger.error(f"JavaScript搜索失败: {str(e)}")

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

            # 先等待一段时间，让页面响应
            await asyncio.sleep(3)

            # 尝试等待页面加载完成
            await self.page.wait_for_load_state("networkidle")

            # 方案1: 查找modal弹窗并处理
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
            ".el-message-box"
        ]

        for selector in modal_selectors:
            try:
                # 增加等待时间，给modal更多出现时间
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    is_visible = await element.is_visible()
                    if is_visible:
                        self.logger.info(f"找到modal弹窗，选择器: {selector}")
                        return element
            except:
                continue

        return None

    async def _handle_modal_confirmation(self, modal_element: Any) -> bool:
        """处理modal弹窗的确认操作"""
        # 在modal中查找确认导出按钮 - 使用更多选择器
        confirm_selectors = [
            "button:has-text('确认导出')",
            "button:has-text('确认')",
            "button:has-text('导出')",
            ".ivu-btn-primary:has-text('确认')",
            ".ivu-btn-text:has-text('确认')",
            ".confirm-btn",
            ".btn-primary",
            ".btn-confirm",
            "[class*='confirm']",
            "[class*='primary']",
            "button[type='submit']",
            ".el-button--primary",
            ".el-button--default"
        ]

        confirm_button = None

        # 首先在modal内查找
        if hasattr(modal_element, 'query_selector_all'):
            modal_buttons = await modal_element.query_selector_all("button")
            self.logger.info(f"在modal中找到 {len(modal_buttons)} 个按钮")

            for i, button in enumerate(modal_buttons):
                try:
                    text = await button.text_content()
                    self.logger.debug(f"Modal按钮 {i+1}: '{text}'")

                    if text and ("确认" in text or "导出" in text):
                        is_visible = await button.is_visible()
                        if is_visible:
                            confirm_button = button
                            self.logger.info(f"找到确认按钮，文本: '{text}'")
                            break
                except:
                    continue

        # 如果modal内没找到，全局查找确认按钮
        if not confirm_button:
            self.logger.info("在modal内未找到确认按钮，尝试全局查找...")
            for selector in confirm_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=3000)
                    if button:
                        text = await button.text_content()
                        self.logger.debug(f"全局查找按钮 '{selector}': '{text}'")

                        if text and ("确认" in text or "导出" in text):
                            is_visible = await button.is_visible()
                            if is_visible:
                                confirm_button = button
                                self.logger.info(f"全局找到确认按钮，选择器: {selector}, 文本: '{text}'")
                                break
                except:
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

        # 等待一段时间，看是否有下载开始
        await asyncio.sleep(3)

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
                ".el-notification"
            ]

            for indicator in download_indicators:
                elements = await self.page.query_selector_all(indicator)
                for element in elements:
                    if await element.is_visible():
                        text = await element.text_content()
                        if text and ("导出" in text or "下载" in text):
                            self.logger.info(f"发现下载提示: {text}")
                            return True
        except:
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
            await self.navigate_to(self.target_url)

            # 执行导出流程
            filter_element = await self.find_filter_section()
            export_button = await self.find_export_button(filter_element)
            dropdown_element = await self.show_and_find_dropdown(export_button)
            dropdown_item = await self.find_dropdown_item(dropdown_element)

            # 点击dropdown-item
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
                use_task_center=True  # 使用任务中心模式（适用于大文件导出）
            )

            self.logger.info(f"商品档案导出完成，文件保存路径: {download_path}")
            return download_path

        except Exception as e:
            self.logger.error(f"商品档案导出失败: {str(e)}")
            await self.take_screenshot("goods_archive_error.png")
            raise