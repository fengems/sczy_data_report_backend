"""
Base crawler class
"""
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextlib import asynccontextmanager

from playwright.async_api import Page, Browser, BrowserContext, async_playwright

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

    async def _init_browser(self, context_options: Optional[Dict[str, Any]] = None) -> None:
        """Initialize browser

        Args:
            context_options: Optional context configuration. If None, uses default settings.
                           Example: {"viewport": {"width": 1920, "height": 1080}, "user_agent": "..."}
        """
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=settings.browser_headless,
                args=[],  # 使用默认参数，不添加任何特殊配置
                channel="chrome"  # 使用Chrome浏览器
            )

            # Create browser context - use default settings unless specific options provided
            if context_options:
                self.context = await self.browser.new_context(**context_options)
                self.logger.info(f"Browser context created with custom options: {context_options}")
            else:
                self.context = await self.browser.new_context()  # Use all defaults
                self.logger.info("Browser context created with default settings")

            # Create page
            self.page = await self.context.new_page()

            # Set download path
            if self.page and self.page.context:
                await self.page.context.set_extra_http_headers({
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
                })

            self.logger.info("Browser initialized successfully")

            # 如果不是headless模式，添加一些调试便利功能
            if not settings.browser_headless:
                await self._setup_debug_features()

    async def use_existing_context(self, browser_context: BrowserContext) -> None:
        """Use an existing browser context instead of creating a new one

        Args:
            browser_context: An existing browser context to reuse
        """
        self.context = browser_context
        self.browser = browser_context.browser
        self.page = await self.context.new_page()

        self.logger.info("Using existing browser context")

        # 如果不是headless模式，添加调试功能
        if not settings.browser_headless:
            await self._setup_debug_features()

    async def _setup_debug_features(self) -> None:
        """设置调试模式下的便利功能"""
        try:
            # 添加一些JavaScript代码，方便调试
            if self.page:
                await self.page.add_init_script("""
                // 添加全局调试函数
                window.debugScroll = function(x = 0, y = 0) {
                    window.scrollTo(x, y);
                    console.log(`Scrolled to (${x}, ${y})`);
                };

                // 添加页面信息显示
                window.debugInfo = function() {
                    console.log('Page Info:', {
                        url: window.location.href,
                        title: document.title,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        scroll: {
                            x: window.scrollX,
                            y: window.scrollY
                        }
                    });
                };

                // 添加高亮元素功能
                window.debugHighlight = function(selector) {
                    const element = document.querySelector(selector);
                    if (element) {
                        element.style.border = '3px solid red';
                        element.style.backgroundColor = 'yellow';
                        console.log(`Highlighted: ${selector}`);
                        return element;
                    }
                    console.log(`Element not found: ${selector}`);
                    return null;
                };

                console.log('Debug functions loaded. Use debugScroll(), debugInfo(), debugHighlight()');
            """)

            self.logger.info("Debug features enabled")
        except Exception as e:
            self.logger.warning(f"Failed to setup debug features: {str(e)}")

    async def resize_window(self, width: int, height: int) -> None:
        """动态调整窗口大小"""
        if not self.page:
            self.logger.warning("Cannot resize window: page not initialized")
            return

        try:
            await self.page.set_viewport_size({"width": width, "height": height})
            self.logger.info(f"Window resized to {width}x{height}")
        except Exception as e:
            self.logger.error(f"Failed to resize window: {str(e)}")

    async def get_window_size(self) -> dict:
        """获取当前窗口大小"""
        if not self.page:
            return {"width": 0, "height": 0}

        try:
            size = await self.page.evaluate("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            """)
            return size
        except Exception as e:
            self.logger.error(f"Failed to get window size: {str(e)}")
            return {"width": 0, "height": 0}

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
            if element:
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

    def _safe_page_call(self, method_name: str, *args, **kwargs):
        """安全地调用page方法的辅助函数"""
        if not self.page:
            self.logger.warning(f"Cannot call {method_name}: page not initialized")
            return None
        try:
            method = getattr(self.page, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error calling page.{method_name}: {str(e)}")
            return None

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

    async def take_screenshot(self, filename: Optional[str] = None) -> str:
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
        """检查登录状态"""
        if not self.page:
            return False

        try:
            # 检查当前URL是否为目标URL
            current_url = self.page.url
            target_url = "https://scm.sdongpo.com/cc_sssp/superAdmin/viewCenter/v1/index"

            if current_url == target_url:
                self.logger.info(f"Login status confirmed: at target URL {current_url}")
                return True

            # 检查URL是否包含目标路径的特征
            if "/v1/index" in current_url and "viewCenter" in current_url:
                self.logger.info(f"Login status confirmed: URL contains target patterns {current_url}")
                return True

            self.logger.info(f"Not logged in yet: current URL {current_url}")
            return False

        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False

    @abstractmethod
    async def login(self) -> bool:
        """Login to ERP system - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def crawl_data(self, params: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Crawl data - must be implemented by subclasses"""
        pass

    async def run(self, params: Optional[Dict[str, Any]] = None) -> Union[str, Dict[str, Any]]:
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