# 变更日志

本文档记录了项目的所有重要变更，按时间顺序排列。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

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