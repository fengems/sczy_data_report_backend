"""
任务中心工具模块
用于处理ERP系统中的大文件导出任务
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.utils.logger import get_logger


class TaskCenterUtils:
    """任务中心工具类"""

    def __init__(self, page: Any):
        self.page = page
        self.logger = get_logger("task_center")
        self._temp_url = None  # 临时存储下载URL

    def _generate_timestamped_filename(self, base_filename: str) -> str:
        """
        生成带时间戳的文件名

        Args:
            base_filename: 基础文件名（不包含扩展名）

        Returns:
            str: 带时间戳的文件名
        """
        # 获取当前时间，格式为 YYYYMMDDHHMMSS
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{base_filename}_{timestamp}"

    async def wait_for_export_task(
        self,
        filename: Optional[str] = None,
        timeout: int = 300,
        use_task_center: bool = True,
    ) -> str:
        """
        等待导出任务完成并下载文件

        Args:
            filename: 可选的文件名，如果提供则用于命名下载的文件
            timeout: 超时时间（秒），默认5分钟
            use_task_center: 是否使用任务中心，默认True。如果为False，则直接等待下载

        Returns:
            str: 下载文件的完整路径
        """
        try:
            self.logger.info("开始处理导出任务...")

            if use_task_center:
                # 方案1: 使用任务中心监听（适用于大文件导出）
                self.logger.info("使用任务中心模式...")
                task_drawer = await self._open_task_drawer()
                return await self._wait_by_page_elements(task_drawer, filename, timeout)
            else:
                # 方案2: 直接等待下载（适用于直接导出文件）
                self.logger.info("使用直接下载模式...")
                return await self._wait_for_direct_download(filename, timeout)

        except Exception as e:
            self.logger.error(f"等待导出任务失败: {str(e)}")
            raise

    async def _open_task_drawer(self) -> Any:
        """
        打开任务中心抽屉
        检查是否已自动弹出，如果没有则手动点击任务按钮
        """
        try:
            self.logger.info("检查任务中心抽屉状态...")

            # 等待1秒，让可能的自动弹窗显示
            await asyncio.sleep(1)

            # 检查是否已经有抽屉显示
            try:
                existing_drawer = await self.page.wait_for_selector(
                    ".task-drawer", timeout=3000
                )
                if existing_drawer and await existing_drawer.is_visible():
                    self.logger.info("任务中心抽屉已自动弹出")
                    return existing_drawer
            except Exception:
                pass

            # 如果没有自动弹出，手动点击任务按钮
            self.logger.info("未找到自动弹出的抽屉，尝试手动打开任务中心...")

            # 查找任务按钮
            task_selectors = [
                ".task-btn:has-text('任务')",
                ".task-btn:has-text('任务中心')",
                "[class*='task-btn']:has-text('任务')",
                "button:has-text('任务')",
                "[class*='task']:has-text('任务')",
            ]

            task_button = None
            for selector in task_selectors:
                try:
                    task_button = await self.page.wait_for_selector(
                        selector, timeout=5000
                    )
                    if task_button and await task_button.is_visible():
                        self.logger.info(f"找到任务按钮，选择器: {selector}")
                        break
                except Exception:
                    continue

            if not task_button:
                # 备用方案：查找所有按钮，寻找包含"任务"文本的
                all_buttons = self.page.locator("button, [class*='btn'], [role='button']")
                button_count = await all_buttons.count()
                for i in range(button_count):
                    try:
                        button = all_buttons.nth(i)
                        text = await button.text_content()
                        if text and "任务" in text.strip():
                            is_visible = await button.is_visible()
                            if is_visible:
                                task_button = button
                                self.logger.info("通过文本匹配找到任务按钮")
                                break
                    except Exception:
                        continue

            if not task_button:
                raise RuntimeError("无法找到任务中心按钮")

            # 点击任务按钮
            await task_button.click()
            self.logger.info("已点击任务中心按钮")

            # 等待抽屉出现
            await asyncio.sleep(2)

            # 获取抽屉元素
            drawer = await self.page.wait_for_selector(".task-drawer", timeout=10000)
            if not drawer or not await drawer.is_visible():
                raise RuntimeError("任务中心抽屉未成功打开")

            self.logger.info("任务中心抽屉已成功打开")
            return drawer

        except Exception as e:
            self.logger.error(f"打开任务中心抽屉失败: {str(e)}")
            raise

    async def _wait_for_direct_download(
        self, filename: Optional[str], timeout: int
    ) -> str:
        """
        直接等待文件下载（适用于不弹出任务中心的导出）

        Args:
            filename: 可选的文件名
            timeout: 超时时间

        Returns:
            str: 下载文件的完整路径
        """
        try:
            self.logger.info("等待直接下载文件...")

            # 设置下载监听
            download_promise = self.page.wait_for_event("download", timeout=timeout)

            # 等待下载完成
            download = await download_promise

            # 确定文件名
            final_filename = None
            if filename:
                # 使用提供的文件名，并添加时间戳，保持原扩展名
                original_name = download.suggested_filename
                if original_name and "." in original_name:
                    extension = original_name.split(".")[-1]
                    timestamped_name = self._generate_timestamped_filename(filename)
                    final_filename = f"{timestamped_name}.{extension}"
                else:
                    # 如果原文件没有扩展名，直接添加时间戳
                    final_filename = self._generate_timestamped_filename(filename)
            else:
                # 如果没有提供文件名，使用原始文件名并添加时间戳
                original_name = download.suggested_filename
                if original_name:
                    name_without_ext = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
                    extension = original_name.split(".")[-1] if "." in original_name else ""
                    timestamped_name = self._generate_timestamped_filename(name_without_ext)
                    final_filename = f"{timestamped_name}.{extension}" if extension else timestamped_name
                else:
                    final_filename = self._generate_timestamped_filename("downloaded_file")

            if not final_filename:
                final_filename = self._generate_timestamped_filename("downloaded_file")

            # 确保下载目录存在
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)

            # 保存文件
            download_path = download_dir / final_filename
            await download.save_as(download_path)

            self.logger.info(f"直接下载成功: {download_path}")
            return str(download_path)

        except Exception as e:
            self.logger.error(f"直接下载失败: {str(e)}")
            raise

    async def _wait_by_page_elements(
        self, task_drawer: Any, filename: Optional[str], timeout: int
    ) -> str:
        """
        通过页面元素监听任务状态并点击下载

        Args:
            task_drawer: 任务抽屉元素
            filename: 可选的文件名
            timeout: 超时时间

        Returns:
            str: 下载文件的完整路径
        """
        try:
            self.logger.info("监听任务中心状态，等待任务完成...")

            # 查找任务列表
            task_list = await task_drawer.wait_for_selector(
                ".task-drawer-list", timeout=10000
            )
            if not task_list:
                raise RuntimeError("未找到任务列表")

            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    # 获取第一个任务项
                    first_item = await task_list.wait_for_selector(
                        ".items", timeout=5000
                    )
                    if not first_item:
                        self.logger.debug("未找到任务项，等待3秒...")
                        await asyncio.sleep(3)
                        continue

                    # 查找图标元素
                    icons_element = await first_item.wait_for_selector(
                        "div.icons", timeout=3000
                    )
                    if not icons_element:
                        self.logger.debug("未找到图标元素，等待3秒...")
                        await asyncio.sleep(3)
                        continue

                    # 检查图标状态
                    class_name = await icons_element.get_attribute("class")

                    if "loading" in class_name:
                        self.logger.info("任务正在处理中...")
                        await asyncio.sleep(5)
                        continue
                    elif "download" in class_name:
                        self.logger.info("任务已完成，点击下载...")
                        return await self._click_and_download(first_item, filename)
                    else:
                        self.logger.debug(f"任务状态: {class_name}，等待...")
                        await asyncio.sleep(3)
                        continue

                except Exception as e:
                    self.logger.debug(f"检查任务状态时出错: {str(e)}")
                    await asyncio.sleep(3)
                    continue

            raise RuntimeError(f"等待任务完成超时 ({timeout}秒)")

        except Exception as e:
            self.logger.error(f"任务中心监听失败: {str(e)}")
            raise

    async def _click_and_download(
        self, download_element: Any, filename: Optional[str]
    ) -> str:
        """
        点击下载元素并处理文件下载

        Args:
            download_element: 可点击的下载元素
            filename: 可选的文件名

        Returns:
            str: 下载文件的完整路径
        """
        try:
            self.logger.info("准备下载文件...")

            # 设置下载监听
            download_promise = self.page.wait_for_event("download", timeout=30000)

            # 尝试多种点击策略处理模态框遮罩问题
            success = False
            last_error = None

            # 策略1: 尝试移除可能阻挡的模态框遮罩
            try:
                self.logger.info("尝试移除模态框遮罩...")
                await self.page.evaluate("""
                    // 移除可能的模态框遮罩
                    const modals = document.querySelectorAll('.ivu-modal-wrap, .ivu-modal-mask');
                    modals.forEach(modal => {
                        if (modal.style) {
                            modal.style.display = 'none';
                            modal.style.visibility = 'hidden';
                            modal.style.zIndex = '-1';
                        }
                    });
                """)
                await asyncio.sleep(0.2)
                await download_element.click()
                self.logger.info("策略1成功：移除遮罩后点击成功")
                success = True
            except Exception as e:
                self.logger.debug(f"策略1失败: {str(e)}")
                last_error = e

            # 策略2: 强制点击并绕过事件拦截
            if not success:
                try:
                    self.logger.info("尝试强制点击并绕过事件拦截...")
                    await download_element.evaluate("""
                        (element) => {
                            // 移除pointer-events样式
                            element.style.pointerEvents = 'auto';
                            element.style.zIndex = '9999';
                            // 触发原生点击事件
                            element.click();
                        }
                    """)
                    self.logger.info("策略2成功：强制点击成功")
                    success = True
                except Exception as e:
                    self.logger.debug(f"策略2失败: {str(e)}")
                    last_error = e

            # 策略3: 模拟鼠标事件序列
            if not success:
                try:
                    self.logger.info("尝试模拟完整鼠标事件序列...")
                    await download_element.hover()
                    await asyncio.sleep(0.1)
                    await download_element.dispatchEvent("mousedown")
                    await asyncio.sleep(0.05)
                    await download_element.dispatchEvent("mouseup")
                    await asyncio.sleep(0.05)
                    await download_element.dispatchEvent("click")
                    self.logger.info("策略3成功：模拟鼠标事件成功")
                    success = True
                except Exception as e:
                    self.logger.debug(f"策略3失败: {str(e)}")
                    last_error = e

            # 策略4: 使用JavaScript直接触发下载
            if not success:
                try:
                    self.logger.info("尝试JavaScript直接触发...")
                    # 获取元素的onclick事件或href
                    click_result = await download_element.evaluate("""
                        (element) => {
                            // 尝试获取链接或触发点击
                            if (element.href) {
                                window.open(element.href, '_blank');
                                return 'href_triggered';
                            }
                            if (element.onclick) {
                                element.onclick();
                                return 'onclick_triggered';
                            }
                            // 创建新的点击事件
                            const event = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            element.dispatchEvent(event);
                            return 'event_dispatched';
                        }
                    """)
                    self.logger.info(f"策略4成功：JavaScript触发成功 - {click_result}")
                    success = True
                except Exception as e:
                    self.logger.debug(f"策略4失败: {str(e)}")
                    last_error = e

            if not success:
                error_msg = f"所有点击策略都失败，最后一个错误: {str(last_error) if last_error else 'Unknown error'}"
                self.logger.warning(error_msg)
                raise Exception(error_msg)

            # 等待下载完成
            download = await download_promise

            # 确定文件名
            final_filename = None
            if filename:
                # 使用提供的文件名，并添加时间戳，保持原扩展名
                original_name = download.suggested_filename
                if original_name and "." in original_name:
                    extension = original_name.split(".")[-1]
                    timestamped_name = self._generate_timestamped_filename(filename)
                    final_filename = f"{timestamped_name}.{extension}"
                else:
                    # 如果原文件没有扩展名，直接添加时间戳
                    final_filename = self._generate_timestamped_filename(filename)
            else:
                # 如果没有提供文件名，使用原始文件名并添加时间戳
                original_name = download.suggested_filename
                if original_name:
                    name_without_ext = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
                    extension = original_name.split(".")[-1] if "." in original_name else ""
                    timestamped_name = self._generate_timestamped_filename(name_without_ext)
                    final_filename = f"{timestamped_name}.{extension}" if extension else timestamped_name
                else:
                    final_filename = self._generate_timestamped_filename("downloaded_file")

            if not final_filename:
                final_filename = self._generate_timestamped_filename("downloaded_file")

            # 确保下载目录存在
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)

            # 保存文件
            download_path = download_dir / final_filename
            await download.save_as(download_path)

            self.logger.info(f"文件下载成功: {download_path}")
            return str(download_path)

        except Exception as e:
            self.logger.error(f"点击下载失败: {str(e)}")
            raise


async def wait_for_export_task(
    page: Any,
    filename: Optional[str] = None,
    timeout: int = 300,
    use_task_center: bool = True,
) -> str:
    """
    便捷函数：等待导出任务完成并下载文件

    Args:
        page: Playwright页面对象
        filename: 可选的文件名
        timeout: 超时时间（秒）
        use_task_center: 是否使用任务中心，默认True。如果为False，则直接等待下载

    Returns:
        str: 下载文件的完整路径
    """
    task_utils = TaskCenterUtils(page)
    return await task_utils.wait_for_export_task(filename, timeout, use_task_center)
