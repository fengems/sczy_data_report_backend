"""
ERP authentication module
"""
import asyncio
from typing import Dict, Any

from app.crawlers.base import BaseCrawler
from app.config.settings import settings
from app.utils.logger import get_logger


class ERPAuthCrawler(BaseCrawler):
    """ERP system authentication crawler"""

    def __init__(self):
        super().__init__("erp_auth")

    async def login(self) -> bool:
        """
        Login to ERP system
        实现具体的ERP登录逻辑 - 适配SPA单页面应用
        """
        try:
            # 导航到登录页面
            await self.navigate_to(settings.erp_login_page)
            self.logger.info(f"Navigated to login page: {settings.erp_base_url}{settings.erp_login_page}")

            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle")

            # 对于SPA应用，需要等待JavaScript渲染完成
            # 等待root-master元素被填充内容
            self.logger.info("等待SPA页面渲染完成...")

            # 等待最多30秒让JavaScript完成渲染
            max_wait_time = 30
            wait_interval = 1
            waited_time = 0

            while waited_time < max_wait_time:
                # 检查是否有input元素出现
                inputs = await self.page.query_selector_all("input")
                if len(inputs) > 0:
                    self.logger.info(f"SPA渲染完成，找到{len(inputs)}个input元素")
                    break

                await asyncio.sleep(wait_interval)
                waited_time += wait_interval
                self.logger.debug(f"等待SPA渲染... {waited_time}/{max_wait_time}秒")

            if waited_time >= max_wait_time:
                raise RuntimeError("SPA页面渲染超时，未能找到登录表单元素")

            # 查找用户名输入框 - 通过"请输入用户名"文本定位
            username_selectors = [
                'input[placeholder*="请输入用户名"]',
                'input[placeholder*="用户名"]',
                'input[type="text"]',
                '#username',
                '.username-input',
                'input[placeholder*="账号"]',
                'input[placeholder*="用户"]'
            ]

            username_input = None
            found_selector = None

            for selector in username_selectors:
                try:
                    username_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if username_input:
                        found_selector = selector
                        self.logger.info(f"找到用户名输入框，选择器: {selector}")
                        break
                except:
                    continue

            if not username_input:
                # 如果还是没找到，打印更多信息用于调试
                all_inputs = await self.page.query_selector_all("input")
                self.logger.warning(f"未找到用户名输入框。页面中总共有{len(all_inputs)}个input元素")
                for i, inp in enumerate(all_inputs):
                    try:
                        placeholder = await inp.get_attribute("placeholder")
                        input_type = await inp.get_attribute("type")
                        name = await inp.get_attribute("name")
                        self.logger.debug(f"Input {i+1}: type={input_type}, name={name}, placeholder={placeholder}")
                    except:
                        pass
                raise RuntimeError("未找到用户名输入框")

            # 填充用户名 (fill方法会自动清空现有内容)
            await username_input.fill(settings.erp_username)
            self.logger.info(f"用户名已填写: {settings.erp_username}")

            # 查找密码输入框 - 通过"请输入密码"文本定位
            password_selectors = [
                'input[placeholder*="请输入密码"]',
                'input[placeholder*="密码"]',
                'input[type="password"]',
                '#password',
                '.password-input',
                'input[placeholder*="pass"]'
            ]

            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        self.logger.info(f"找到密码输入框，选择器: {selector}")
                        break
                except:
                    continue

            if not password_input:
                raise RuntimeError("未找到密码输入框")

            # 填充密码 (fill方法会自动清空现有内容)
            await password_input.fill(settings.erp_password)
            self.logger.info("密码已填写")

            # 查找并点击登录按钮 - 通过classname为"loginBtn"的button元素
            login_button_selectors = [
                'button.loginBtn',
                '.loginBtn',
                'button[class*="loginBtn"]',
                'button:has-text("登录")',
                'button:has-text("登 录")',
                'button:has-text("登陆")',
                '.login-button',
                '#login-button',
                'button[type="submit"]',
                'button[class*="login"]',
                'button[class*="submit"]'
            ]

            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = await self.page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        self.logger.info(f"找到登录按钮，选择器: {selector}")
                        break
                except:
                    continue

            if not login_button:
                # 调试：打印所有button信息
                all_buttons = await self.page.query_selector_all("button")
                self.logger.warning(f"未找到登录按钮。页面中总共有{len(all_buttons)}个button元素")
                for i, btn in enumerate(all_buttons):
                    try:
                        text = await btn.text_content()
                        class_name = await btn.get_attribute("class")
                        self.logger.debug(f"Button {i+1}: text={text}, class={class_name}")
                    except:
                        pass
                raise RuntimeError("未找到登录按钮")

            # 点击登录按钮
            await login_button.click()
            self.logger.info("已点击登录按钮")

            # 等待页面跳转 - 等待URL变成目标地址
            target_url = "https://scm.sdongpo.com/cc_sssp/superAdmin/viewCenter/v1/index"
            try:
                # 等待URL跳转，最多等待30秒
                await self.page.wait_for_url(
                    target_url,
                    timeout=30000,
                    wait_until="networkidle"
                )
                self.logger.info(f"成功跳转到目标URL: {target_url}")
                return True
            except Exception as url_error:
                # 检查当前URL是否已经是目标URL
                current_url = self.page.url
                if current_url == target_url:
                    self.logger.info(f"已经在目标URL: {current_url}")
                    return True
                else:
                    # 检查是否包含错误信息
                    try:
                        # 查找可能的错误提示元素
                        error_selectors = [
                            '.error-message',
                            '.alert-error',
                            '[class*="error"]',
                            '[class*="alert"]',
                            '.ant-message-error',
                            '.ant-form-item-explain-error'
                        ]

                        for error_selector in error_selectors:
                            error_element = await self.page.query_selector(error_selector)
                            if error_element:
                                error_text = await error_element.text_content()
                                if error_text and error_text.strip():
                                    self.logger.error(f"登录错误信息: {error_text}")
                                    raise RuntimeError(f"登录失败: {error_text}")
                    except:
                        pass

                    raise RuntimeError(f"登录失败：未能成功跳转到目标URL。当前URL: {current_url}")

        except Exception as e:
            self.logger.error(f"登录错误: {str(e)}")
            # 截图保存当前页面状态用于调试
            try:
                screenshot_path = await self.take_screenshot("login_error.png")
                self.logger.info(f"登录错误截图已保存: {screenshot_path}")
            except:
                pass
            raise

    async def _handle_captcha(self) -> None:
        """
        Handle captcha (if ERP system has captcha)
        Implement different captcha handling solutions based on specific situations
        """
        # Example: Wait for manual captcha input
        # captcha_element = await self.wait_for_element("#captcha")
        # if captcha_element:
        #     await self.page.pause()  # Pause to let user manually input captcha
        pass

    async def crawl_data(self, params: Dict[str, Any]) -> str:
        """
        Auth module doesn't crawl data directly, only handles login
        """
        return "Authentication completed"

    async def logout(self) -> bool:
        """
        Logout from system
        """
        try:
            # Find and click logout button
            logout_selectors = [
                "#logout",
                "[data-testid='logout']",
                ".logout-button",
                "a[href*='logout']"
            ]

            for selector in logout_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await self.page.wait_for_load_state("networkidle")
                        self.logger.info("Logout successful")
                        return True
                except:
                    continue

            self.logger.warning("Logout button not found")
            return False

        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            return False