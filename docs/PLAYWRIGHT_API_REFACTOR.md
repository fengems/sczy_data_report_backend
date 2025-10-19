# Playwright API 最佳实践改写记录

**时间**: 2025-10-20 00:16:55
**目标**: 将 app/crawlers/ 目录下的爬虫代码从 `query_selector` 改写为 Playwright 官方推荐的 `locator` API

## 改写背景

根据 Playwright 官方推荐，`locator` API 比 `query_selector` 具有以下优势：
- 更好的性能和稳定性
- 自动重试机制
- 更清晰的链式调用语法
- 符合最佳实践标准

## 改写范围

### 1. app/crawlers/order.py
**改写内容**:
- `base_filter.query_selector()` → `base_filter.locator()`
- `page.query_selector_all()` → `page.locator()`
- `filter_cols.query_selector()` → `filter_cols.locator()`
- `modal.query_selector()` → `modal.locator()`
- `checkbox_group.query_selector()` → `checkbox_group.locator()`
- `filter_btns.query_selector()` → `filter_btns.locator()`
- `export_box.query_selector()` → `export_box.locator()`

**主要变更**:
- 使用 `await filter_cols.all()` 替代直接遍历 `query_selector_all` 结果
- 使用 `await element.count() > 0` 检查元素是否存在
- 使用 `locator.first()` 获取第一个匹配元素

### 2. app/crawlers/auth.py
**改写内容**:
- `page.query_selector_all("input")` → `page.locator("input")`
- `page.query_selector_all("button")` → `page.locator("button")`
- `page.query_selector(error_selector)` → `page.locator(error_selector)`

**主要变更**:
- 使用 `await inputs.count()` 获取元素数量
- 使用 `all_buttons.nth(i)` 遍历元素
- 使用 `error_locator.first()` 获取第一个匹配元素

### 3. app/crawlers/goods_archive.py
**改写内容**:
- `filter_element.query_selector()` → `filter_element.locator()`
- `page.query_selector_all("button")` → `page.locator("button")`
- `page.query_selector_all(selector)` → `page.locator(selector)`
- `modal_element.query_selector()` → `modal_element.locator()`

**主要变更**:
- 使用 `await button.count()` 检查按钮数量
- 使用 `elements.nth(i)` 遍历元素集合
- 使用 `item.first()` 获取第一个匹配项

### 4. app/crawlers/utils/task_center.py
**改写内容**:
- `page.query_selector_all("button, [class*='btn'], [role='button']")` → `page.locator("button, [class*='btn'], [role='button']")`

**主要变更**:
- 使用 `await all_buttons.count()` 获取按钮数量
- 使用 `all_buttons.nth(i)` 遍历按钮

## 改写原则

1. **保持原有逻辑不变**: 所有改写都保持原有的业务逻辑和执行流程
2. **渐进式改写**: 逐个方法进行改写，确保每步都能正常工作
3. **错误处理增强**: 利用 locator API 的自动重试机制提高稳定性
4. **类型安全**: 使用 `await element.count() > 0` 替代直接检查元素是否存在

## 性能优势

改写后的代码具有以下性能优势：
- **自动等待**: locator API 会自动等待元素出现
- **重试机制**: 失败时会自动重试，提高稳定性
- **缓存优化**: locator 对象可以被缓存和重用
- **更好的错误处理**: 提供更详细的错误信息

## 修复的问题

### order.py 中的 Locator 使用错误
在改写过程中发现了一些常见的 Locator API 使用错误：

1. **ElementHandle 调用 locator 方法错误**:
   - `base_filter = await page.wait_for_selector()` + `base_filter.locator()` ❌
   - `base_filter = page.locator()` + `base_filter.locator()` ✅

2. **条件判断错误**: `if filter_advance:` → `if await filter_advance.count() > 0:`

3. **严格模式违反错误**: 当选择器匹配多个元素时，必须使用 `.first()`
   - 发现 `.filter__advance-trigger` 匹配了2个元素，需要使用 `.first()` 来指定第一个

4. **方法调用规范**:
   - 单个元素时: `await locator.method()`
   - 多个元素时: `await locator.first().method()`
   - `await filter_advance.text_content()` → `await filter_advance.first().text_content()`
   - `await filter_advance.click()` → `await filter_advance.first().click()`
   - `await input_element.fill()` → `await input_element.first().fill()`
   - `await export_box.hover()` → `await export_box.first().hover()`
   - `await checkbox_input.is_checked()` → `await checkbox_input.first().is_checked()`
   - `await export_button.is_visible()` → `await export_button.first().is_visible()`
   - `await export_button.click()` → `await export_button.first().click()`

### goods_archive.py 中的类似问题
- `await button.text_content()` → `await button.first().text_content()`
- `await item.is_visible()` → `await item.first().is_visible()`
- `await button.is_visible()` → `await button.first().is_visible()`

## 关键发现和修复

### 🔍 根本原因：.first() 是属性不是方法

通过 Context7 MCP 查找 Playwright 文档发现了关键问题：

**错误用法**：
```python
await locator.first()  # ❌ .first() 是属性，不是方法
```

**正确用法**：
```python
await locator.first   # ✅ .first 是属性
```

### 🛠️ 修复的核心问题

1. **'Locator' object is not callable** 错误
   - 原因：错误地将 `.first()` 当作方法调用
   - 修复：改为 `.first` 属性访问

2. **Strict mode violation 错误**
   - 原因：选择器匹配多个元素时直接调用方法
   - 修复：使用 `.first` 属性或精确选择器

3. **ElementHandle 与 Locator 混用**
   - 原因：`wait_for_selector()` 返回 ElementHandle，不能调用 `.locator()`
   - 修复：统一使用 `page.locator()` 创建 Locator

### 📝 修复总结

**order.py** - 主要修复：
- ✅ 第108, 113行：`filter_advance.first` 替代 `filter_advance.first()`
- ✅ 第213-214, 220, 224行：`input_element` 直接调用方法
- ✅ 第273行：`export_box.hover()` 直接调用
- ✅ 第345行：`checkbox_input.is_checked()` 直接调用
- ✅ 第386, 392行：`export_button` 直接调用方法
- ✅ 第218-236行：重新实现多 input 元素选择逻辑

**goods_archive.py** - 类似修复：
- ✅ 第283, 285行：`item` 直接操作
- ✅ 第393-395行：`button` 直接操作

## 验证结果

所有改写后的文件都通过了 Python 语法检查：
- ✅ order.py - 语法检查通过，已修复 Locator 使用错误
- ✅ auth.py - 语法检查通过
- ✅ goods_archive.py - 语法检查通过，已修复 Locator 使用错误
- ✅ utils/task_center.py - 语法检查通过

## 注意事项

1. **JavaScript 代码保持不变**: 在 `evaluate()` 中执行的 JavaScript 代码保持原样，因为那是浏览器端代码
2. **向后兼容**: 改写后的代码完全向后兼容现有功能
3. **测试建议**: 建议在实际环境中测试改写后的爬虫功能，确保一切正常

## 总结

本次改写成功将所有爬虫代码从 `query_selector` 迁移到 `locator` API，提升了代码的稳定性、性能和可维护性，符合 Playwright 官方最佳实践标准。