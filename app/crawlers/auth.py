"""
ERP authentication module
"""
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
        Implement login logic based on specific ERP system
        """
        try:
            # Navigate to login page
            await self.navigate_to(settings.erp_login_page)

            # Wait for login form to load
            await self.wait_for_element("#username")
            await self.wait_for_element("#password")

            # Fill username
            await self.page.fill("#username", settings.erp_username)

            # Fill password
            await self.page.fill("#password", settings.erp_password)

            # Handle captcha (if any)
            # await self._handle_captcha()

            # Click login button
            await self.wait_and_click("#login-button")

            # Wait for login to complete
            await self.page.wait_for_load_state("networkidle")

            # Verify login success
            if await self.check_login_status():
                self.logger.info("Login successful")
                return True
            else:
                self.logger.error("Login failed: Invalid credentials")
                return False

        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False

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