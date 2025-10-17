#!/usr/bin/env python3
"""
ERP登录功能测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.crawlers.auth import ERPAuthCrawler
from app.config.settings import settings
from app.utils.logger import setup_logger


async def test_login():
    """测试ERP登录功能"""
    print("🚀 开始测试ERP登录功能...")
    print(f"📍 ERP系统: {settings.erp_base_url}")
    print(f"👤 用户名: {settings.erp_username}")
    print(f"🔧 浏览器模式: {'有头模式' if not settings.browser_headless else '无头模式'}")
    print("-" * 50)

    # 初始化日志系统
    setup_logger()

    # 创建登录爬虫实例
    crawler = ERPAuthCrawler()

    try:
        print("🔄 正在启动浏览器...")

        # 执行登录流程
        async with crawler.browser_session():
            print("📖 浏览器已启动，开始登录流程...")

            # 检查当前是否已经登录
            if await crawler.check_login_status():
                print("✅ 已经处于登录状态")
                return True

            # 先导航到登录页面
            print("🌐 导航到登录页面...")
            await crawler.navigate_to(settings.erp_login_page)

            # 等待页面完全加载，包括可能的JavaScript渲染
            print("⏳ 等待页面加载...")
            await crawler.page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)  # 额外等待5秒让JavaScript有时间渲染

            # 调试：获取页面HTML结构和标题
            page_title = await crawler.page.title()
            current_url = crawler.page.url
            print(f"📄 页面标题: {page_title}")
            print(f"🔗 当前URL: {current_url}")

            # 调试：检查页面内容
            page_content = await crawler.page.content()
            print(f"📝 页面HTML长度: {len(page_content)} 字符")

            # 检查是否有错误页面或跳转
            if "404" in page_content or "页面不存在" in page_content or "找不到" in page_content:
                print("⚠️ 页面可能不存在或出现404错误")

            # 调试：查看页面中所有的input元素
            inputs = await crawler.page.query_selector_all("input")
            print(f"🔍 找到 {len(inputs)} 个input元素:")
            for i, input_elem in enumerate(inputs):
                try:
                    placeholder = await input_elem.get_attribute("placeholder")
                    input_type = await input_elem.get_attribute("type")
                    name = await input_elem.get_attribute("name")
                    id_attr = await input_elem.get_attribute("id")
                    class_name = await input_elem.get_attribute("class")
                    print(f"  {i+1}. Type: {input_type}, Name: {name}, ID: {id_attr}, Class: {class_name}, Placeholder: {placeholder}")
                except:
                    print(f"  {i+1}. 无法获取属性")

            # 调试：查看页面中所有的button元素
            buttons = await crawler.page.query_selector_all("button")
            print(f"🔍 找到 {len(buttons)} 个button元素:")
            for i, button in enumerate(buttons):
                try:
                    text = await button.text_content()
                    class_name = await button.get_attribute("class")
                    print(f"  {i+1}. Text: {text}, Class: {class_name}")
                except:
                    print(f"  {i+1}. 无法获取属性")

            # 调试：检查是否有iframe
            iframes = await crawler.page.query_selector_all("iframe")
            print(f"🔍 找到 {len(iframes)} 个iframe元素")
            for i, iframe in enumerate(iframes):
                try:
                    src = await iframe.get_attribute("src")
                    print(f"  {i+1}. iframe src: {src}")
                except:
                    print(f"  {i+1}. 无法获取iframe属性")

            # 调试：保存页面HTML到文件
            html_file = "temp/debug_page.html"
            Path(html_file).write_text(page_content, encoding='utf-8')
            print(f"💾 页面HTML已保存到: {html_file}")

            # 截图保存当前页面状态
            debug_screenshot = await crawler.take_screenshot("debug_login_page.png")
            print(f"📸 调试截图已保存: {debug_screenshot}")

            # 如果没有找到任何表单元素，再等待一下
            if len(inputs) == 0 and len(buttons) == 0:
                print("⏳ 未找到表单元素，等待更长时间...")
                await asyncio.sleep(10)

                # 再次检查
                inputs = await crawler.page.query_selector_all("input")
                buttons = await crawler.page.query_selector_all("button")
                print(f"🔄 再次检查 - 找到 {len(inputs)} 个input元素, {len(buttons)} 个button元素")

            print("🔐 开始执行登录操作...")
            login_success = await crawler.login()

            if login_success:
                print("🎉 登录成功！")

                # 再次检查登录状态
                if await crawler.check_login_status():
                    print("✅ 登录状态验证通过")

                    # 获取当前页面信息
                    current_url = crawler.page.url
                    page_title = await crawler.page.title()
                    print(f"📄 当前页面: {page_title}")
                    print(f"🔗 当前URL: {current_url}")

                    # 截图保存登录成功状态
                    screenshot_path = await crawler.take_screenshot("login_success.png")
                    print(f"📸 登录成功截图已保存: {screenshot_path}")

                    await asyncio.sleep(10)
                    return True
                else:
                    print("❌ 登录状态验证失败")
                    return False
            else:
                print("❌ 登录失败")
                return False

    except Exception as e:
        print(f"💥 测试过程中发生异常: {str(e)}")

        # 尝试截图保存错误状态
        try:
            if crawler.page:
                screenshot_path = await crawler.take_screenshot("login_error.png")
                print(f"📸 错误状态截图已保存: {screenshot_path}")
        except:
            pass

        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("🧪 ERP登录功能测试")
    print("=" * 60)

    success = await test_login()

    print("-" * 50)
    if success:
        print("🎯 测试结果: 成功 ✅")
        print("🚀 ERP登录功能工作正常，可以进行下一步开发")
    else:
        print("🎯 测试结果: 失败 ❌")
        print("🔧 请检查登录参数或ERP系统页面结构")

    print("=" * 60)

    # 保持浏览器窗口打开一段时间供观察
    if success:
        print("⏰ 浏览器将在10秒后自动关闭...")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())