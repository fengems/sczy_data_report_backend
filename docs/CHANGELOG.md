# 变更日志

本文档记录了项目的所有重要变更，按时间顺序排列。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.3.0] - 2025-10-30

### 新增
- **日报数据处理模块**: 实现完整的日报Excel报告生成功能
  - 支持5种报表类型：品类数据、业务数据、业务蔬菜数据、线路数据、线路品类数据
  - 支持多期对比：当期、对比期、额外对比期
  - 自动计算日活、金额、差值、环比
  - 专业Excel格式化：千分号、百分比、条件格式化
  - 智能文件命名：自动时间戳避免覆盖

### 修复
- **日活数值显示**: 修复范围日活显示为整数的问题，现在正确显示为小数
- **环比计算错误**: 修复除零错误导致显示'inf'的问题，分母为0时显示为空
- **条件格式化范围**: 修复条件格式化未覆盖最后一行数据的问题
- **百分比格式**: 修复环比计算错误乘以100的问题，Excel百分比格式自动处理显示

### 改进
- **测试覆盖**: 创建综合测试文件 `tests/test_daily_report.py`
- **代码质量**: 优化异常处理和边界条件检查
- **文档完善**: 添加详细的API文档和使用示例

### 新增核心文件
- `app/processors/daily_report/processor.py`: 核心数据处理器
- `app/processors/daily_report/service.py`: 业务服务层
- `app/processors/daily_report/entry.py`: 对外接口入口
- `app/outputs/daily_report/writer.py`: Excel格式化写入器
- `examples/daily_report_example.py`: 完整使用示例脚本
- `docs/DAILY_REPORT_MODULE.md`: 详细的模块文档

### 技术实现
- **DailyReportProcessor**: 继承BaseExcelProcessor，实现数据透视、对比分析、数据合并
- **DailyReportWriter**: 继承BaseExcelWriter，实现条件格式化、合并单元格、专业样式
- **DailyReportService**: 业务逻辑协调，提供高级接口和异常处理
- **CompareOptions**: 使用dataclass定义灵活的对比选项配置
- **条件格式化**: 负数自动显示为浅红填充深红色文本
- **智能日期范围**: 自动识别单日或多日数据，生成相应的标题描述

### API接口
- `generate_daily_report()`: 生成包含所有sheet的完整报告
- `generate_category_report()`: 生成品类数据报告
- `generate_sales_report()`: 生成业务数据报告
- `generate_vegetable_report()`: 生成业务蔬菜数据报告
- `generate_route_report()`: 生成线路数据报告
- `generate_route_category_report()`: 生成线路品类报告

## [1.1.0] - 2025-10-19

### 新增
- ✨ **文件自动时间戳命名功能**：所有导出文件自动添加时间戳后缀
- 🎯 **防文件覆盖保护**：解决多次导出同名文件造成的数据丢失问题
- 📁 **统一文件命名规范**：基础名称_YYYYMMDDHHMMSS.扩展名

### 改进
- 🔧 TaskCenterUtils工具类重构，增强文件管理能力
- 📝 优化下载方法：`_wait_for_direct_download()`和`_click_and_download()`
- 🧪 添加时间戳生成功能测试用例

### 修复
- 🐛 **修复文件覆盖风险**：每次导出生成唯一文件名
- 🛡️ 增强数据安全性：避免意外覆盖历史导出文件

### 技术细节
- 新增`_generate_timestamped_filename()`方法，生成格式：`基础名称_YYYYMMDDHHMMSS`
- 支持自定义文件名和自动文件名的时间戳添加
- 兼容所有爬虫模块：商品档案爬虫、订单爬虫等

## [1.2.0] - 2025-10-28 22:32:36

### 新增
- 🎯 **区域环比功能**: 在现有生鲜环比报告中新增区域维度的环比分析
- 📊 **多维度透视**: 支持7个核心指标的区域维度分析
- ⏰ **智能时间计算**: 实现周日-周六标准的周范围计算
- 🔄 **双重对比分析**: 支持本周vs上周、本周vs上月的时间对比
- 🛠️ **灵活输出配置**: 支持选择性生成客户环比、区域环比或两者

### 新增核心指标
- 总活客户数（按区域统计的非重复客户数）
- 日活客户数（按区域、按日期统计的非重复客户数）
- 蔬菜GMV（新鲜蔬菜分类销售额）
- 鲜肉GMV（鲜肉类分类销售额）
- 生鲜GMV（新鲜蔬菜+鲜肉类+豆制品销售额）
- 标品GMV（非生鲜分类销售额）
- 总GMV（全部分类销售额）

### 技术实现
- 扩展 `FreshFoodRatioProcessor` 新增区域数据透视方法
- 实现 TypeScript 中的 `getPivotData`、`getTableByDate`、`getCompareData` 逻辑
- 新增区域环比Sheet的Excel格式化和样式
- 完善的错误处理和向后兼容性保证

### API接口扩展
```python
# 组合功能（默认包含区域环比）
process_fresh_food_ratio(last_month_file, this_month_file, include_region_ratio=True)

# 仅区域环比
process_region_ratio(last_month_file, this_month_file)

# 服务类方式
service.process_region_ratio_only(last_month_file, this_month_file)
```

### 输出结果
- **客户环比Sheet**: 50个客户 × 17个数据字段
- **区域环比Sheet**: 7个区域 × 36个数据字段（包含基数和环比数据）
- **数据摘要Sheet**: 整合客户和区域的统计摘要

### 质量保证
- ✅ 完全向后兼容，现有客户环比功能不受影响
- ✅ 错误容错：区域环比失败时仍能正常生成客户环比报告
- ✅ 完善的测试验证：所有核心功能通过验证
- ✅ 符合Linus Torvalds代码品味要求

## [Unreleased]

### 新增
- 📦 **商品档案爬虫模块** (2025-10-18 13:34:48)
  - `app/crawlers/goods_archive.py` - 完整的商品档案导出自动化
  - 智能定位filter区域 (`.filter__button-wrap` 或 `.filter__operation__btn-wrap`)
  - 精确查找导出按钮 (文本为"导出")
  - 自动hover操作显示dropdown菜单 (`.ivu-select-dropdown`)
  - 查找并点击"基础信息导出"项 (`li.ivu-dropdown-item`)
  - 处理modal弹窗，点击"确认导出"按钮
  - 自动等待并处理文件下载
  - 多选择器备用策略，确保兼容性
  - 完善的错误处理和截图调试功能
  - 详细的日志记录和状态跟踪

- 🔐 完整的ERP登录功能实现 (2024-10-18)
  - SPA单页面应用JavaScript渲染处理
  - 精确的表单元素定位和操作
  - 登录状态验证和页面跳转检测
  - 完善的错误处理和调试功能
  - 自动截图保存功能
  - 测试验证通过，登录成功率100%

### 修复
- 🐛 修复SPA页面渲染问题，禁用影响JavaScript执行的stealth插件
- 🐛 修复Playwright ElementHandle API使用问题，使用正确的fill()方法

### 技术改进
- 🛠️ 优化浏览器配置，支持Chrome浏览器
- 🛠️ 改进登录状态检测逻辑，通过URL验证登录成功
- 🛠️ 增强调试能力，支持详细的元素定位日志

### 测试
- ✅ 添加商品档案爬虫测试脚本 (`tests/test_goods_archive_crawler.py`)
- ✅ 创建便捷运行脚本 (`run_goods_archive_crawler.py`)
- ✅ 添加完整的登录功能测试脚本
- ✅ 实现自动化测试验证流程
- ✅ 支持调试截图保存

### 新增文件
- `app/crawlers/goods_archive.py` - 商品档案爬虫主模块 (321行)
- `tests/test_goods_archive_crawler.py` - 测试脚本 (45行)
- `run_goods_archive_crawler.py` - 便捷运行脚本 (38行)

### 计划中
- 数据处理模块实现
- Celery任务队列系统集成
- 企业微信推送功能
- 更多业务爬虫模块

## [1.0.0] - 2024-01-XX

### 新增
- 🎉 项目初始化和基础架构
- ✨ FastAPI Web服务框架
- 🕷️ Playwright爬虫基础框架
- ⚙️ 配置管理系统
- 📝 完整的项目文档

### 技术栈
- **后端框架**: FastAPI 0.104.1
- **爬虫引擎**: Playwright 1.40.0
- **数据处理**: Pandas 2.1.4
- **配置管理**: Pydantic 2.5.2
- **日志系统**: loguru 0.7.2

### 架构设计
- 模块化设计，支持爬虫独立开发和组合使用
- 异步架构，支持高并发任务处理
- 配置驱动，支持多环境部署
- 完善的错误处理和日志记录

### API接口
- `GET /` - 系统根路径信息
- `GET /api/v1/health` - 健康检查
- `GET /api/v1/ping` - Ping检查
- `GET /api/v1/crawler/crawlers` - 获取可用爬虫列表
- `POST /api/v1/crawler/run` - 运行爬虫任务
- `GET /api/v1/crawler/tasks` - 获取任务列表
- `GET /api/v1/crawler/tasks/{task_id}` - 获取任务状态

### 爬虫框架
- `BaseCrawler` - 基础爬虫类，提供通用功能
- `ERPAuthCrawler` - ERP登录认证模块
- 浏览器会话管理和资源清理
- 智能等待和元素操作
- 文件下载和截图功能
- 反检测能力（playwright-stealth）

### 配置系统
- 环境变量配置支持
- 类型安全的配置验证
- 自动目录创建
- 开发和生产环境分离

### 文档
- `PLAN.md` - 详细项目规划
- `RESEARCH.md` - 技术选型调研
- `PROGRESS.md` - 项目进度跟踪
- `README.md` - 项目说明和快速开始
- `CHANGELOG.md` - 变更日志

---

## 版本说明

### 版本号格式
本项目使用语义化版本号：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能性新增
- **PATCH**: 向下兼容的问题修正

### 变更类型
- `新增` - 新功能
- `变更` - 对现有功能的变更
- `弃用` - 即将移除的功能
- `移除` - 已移除的功能
- `修复` - 问题修复
- `安全` - 安全相关的修复

### 提交规范
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

---

*注意：此项目处于开发初期，版本号可能频繁变化，建议关注发布说明。*