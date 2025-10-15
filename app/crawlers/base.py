"""
Base crawler class
"""
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import asynccontextmanager

from playwright.async_api import Page, Browser, BrowserContext, async_playwright
from playwright_stealth import stealth_async

from app.config.settings import settings
from app.utils.logger import get_logger


class BaseCrawler(ABC):
    """Base crawler class"""

    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"crawler.{name}")
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

    @asynccontextmanager
    async def browser_session(self):
        """Browser session context manager"""
        try:
            await self._init_browser()
            yield self.page
        finally:
            await self._cleanup_browser()

    async def _init_browser(self) -> None:
        """Initialize browser"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=settings.browser_headless,
                args=["--disable-blink-features=AutomationControlled"]
            )

            # Create browser context
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # Create page
            self.page = await self.context.new_page()

            # Apply stealth.js to hide automation features
            await stealth_async(self.page)

            # Set download path
            await self.page.context.set_extra_http_headers({
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            })

            self.logger.info("Browser initialized successfully")

    async def _cleanup_browser(self) -> None:
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        self.page = None
        self.logger.info("Browser cleaned up")

    async def navigate_to(self, url: str) -> None:
        """Navigate to specified URL"""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        full_url = f"{settings.erp_base_url}{url}"
        self.logger.info(f"Navigating to: {full_url}")

        await self.page.goto(full_url, wait_until="networkidle")
        await self.page.wait_for_load_state("networkidle")

    async def wait_and_click(self, selector: str, timeout: int = 10000) -> None:
        """Wait for element and click"""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            await element.click()
            self.logger.debug(f"Clicked element: {selector}")
        except Exception as e:
            self.logger.error(f"Failed to click element {selector}: {str(e)}")
            raise

    async def wait_for_element(self, selector: str, timeout: int = 10000) -> Any:
        """Wait for element to appear"""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return element
        except Exception as e:
            self.logger.error(f"Element not found: {selector}, error: {str(e)}")
            raise

    async def get_element_text(self, selector: str) -> str:
        """Get element text"""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        try:
            element = await self.wait_for_element(selector)
            text = await element.text_content()
            return text.strip() if text else ""
        except Exception as e:
            self.logger.error(f"Failed to get text from {selector}: {str(e)}")
            return ""

    async def wait_for_download(self, timeout: int = 60000) -> str:
        """Wait for file download to complete"""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        try:
            download_promise = self.page.wait_for_event("download", timeout=timeout)
            download = await download_promise

            # Save file to specified path
            download_path = Path(settings.browser_download_path) / download.suggested_filename
            await download.save_as(download_path)

            self.logger.info(f"File downloaded: {download_path}")
            return str(download_path)
        except Exception as e:
            self.logger.error(f"Download failed: {str(e)}")
            raise

    async def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot"""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        if not filename:
            filename = f"{self.name}_{int(asyncio.get_event_loop().time())}.png"

        screenshot_path = Path(settings.temp_path) / filename
        await self.page.screenshot(path=str(screenshot_path), full_page=True)

        self.logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)

    async def check_login_status(self) -> bool:
        """Check login status"""
        # TODO: Implement login status check based on specific ERP system
        # This is just an example implementation
        if not self.page:
            return False

        try:
            # Check for specific elements that appear after login
            # For example: username, logout button, etc.
            logout_element = await self.page.query_selector("[data-testid='logout']")
            return logout_element is not None
        except:
            return False

    @abstractmethod
    async def login(self) -> bool:
        """Login to ERP system - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def crawl_data(self, params: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Crawl data - must be implemented by subclasses"""
        pass

    async def run(self, params: Dict[str, Any] = None) -> Union[str, Dict[str, Any]]:
        """Run complete crawler workflow"""
        if params is None:
            params = {}

        try:
            async with self.browser_session():
                # Check login status, login if not logged in
                if not await self.check_login_status():
                    self.logger.info("Not logged in, attempting to login...")
                    login_success = await self.login()
                    if not login_success:
                        raise RuntimeError("Login failed")
                    self.is_logged_in = True
                    self.logger.info("Login successful")
                else:
                    self.logger.info("Already logged in")
                    self.is_logged_in = True

                # Execute data crawling
                result = await self.crawl_data(params)
                self.logger.info("Crawling completed successfully")
                return result

        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")
            raise