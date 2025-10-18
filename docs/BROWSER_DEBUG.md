# 浏览器调试功能说明

本文档描述了爬虫系统的浏览器调试功能和配置优化。

## 🎯 配置优化

### 视口自适应
- **视口设置**: `viewport=None` - 支持窗口大小自适应
- **启动参数**: `--start-maximized` - 浏览器启动时最大化
- **用户体验**: 窗口大小会跟随您的手动调整

### 调试增强
- **User-Agent**: 使用Mac Chrome用户代理，更接近真实环境
- **扩展禁用**: 禁用浏览器扩展，避免干扰
- **信息栏隐藏**: 提供更干净的调试界面

## 🔧 调试工具

### JavaScript调试函数

在浏览器控制台中可使用以下调试函数：

#### `debugInfo()`
显示当前页面信息：
```javascript
debugInfo()
// 输出：页面URL、标题、视口大小、滚动位置
```

#### `debugScroll(x, y)`
滚动到指定位置：
```javascript
debugScroll(0, 500)  // 滚动到页面顶部下方500px
debugScroll()        // 滚动到页面顶部
```

#### `debugHighlight(selector)`
高亮显示指定元素：
```javascript
debugHighlight('.filter__button-wrap')  // 高亮filter按钮区域
debugHighlight('#username')              // 高亮用户名输入框
```

### 爬虫调试方法

#### 获取窗口大小
```python
size = await crawler.get_window_size()
print(f"窗口大小: {size}")
```

#### 调整窗口大小
```python
await crawler.resize_window(1200, 800)  # 调整为1200x800
```

#### 截图调试
```python
screenshot_path = await crawler.take_screenshot("debug_page.png")
```

## 🚀 使用建议

### 1. 调试模式运行
确保 `.env` 文件中设置：
```
browser_headless=false
```

### 2. 窗口调整
- 启动后可以手动调整浏览器窗口大小
- 爬虫会自动适应新的窗口大小
- 使用 `resize_window()` 方法可以程序化调整

### 3. 元素定位调试
- 使用 `debugHighlight()` 快速定位页面元素
- 配合浏览器的开发者工具检查元素
- 验证CSS选择器是否正确

### 4. 页面交互调试
- 使用 `debugScroll()` 快速跳转到页面不同位置
- 使用 `debugInfo()` 获取页面当前状态信息

## 📁 相关文件

- `app/crawlers/base.py` - 基础爬虫类，包含浏览器配置
- `scripts/test_browser_config.py` - 浏览器配置测试脚本
- `scripts/README.md` - 脚本使用说明

## ⚠️ 注意事项

1. **调试模式**: 仅在非headless模式下启用调试功能
2. **性能影响**: 调试功能可能会影响爬虫性能，生产环境建议关闭
3. **浏览器版本**: 不同浏览器版本可能表现略有差异
4. **系统兼容**: macOS用户获得最佳体验，其他系统可能需要调整参数

---

*最后更新: 2025-10-18*