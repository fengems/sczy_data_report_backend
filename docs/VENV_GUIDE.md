# 虚拟环境使用指南

## 🎯 概述

本项目使用Python虚拟环境来隔离依赖，确保开发环境的一致性和可移植性。

## 📁 环境结构

```
sczy_data_report_backend/
├── venv/                    # 虚拟环境目录
│   ├── bin/                # 可执行文件（Linux/Mac）
│   ├── lib/                # Python库
│   └── include/            # C头文件
├── .env                    # 环境配置文件
├── .env.example           # 配置文件模板
├── requirements.txt       # 依赖列表
├── setup.sh               # 环境设置脚本
└── start.sh               # 服务启动脚本
```

## 🚀 快速开始

### 首次设置

如果你是第一次设置环境，运行：

```bash
./setup.sh
```

这个脚本会自动：
- 检查Python版本
- 创建虚拟环境
- 安装所有依赖
- 安装Playwright浏览器
- 创建必要的目录
- 生成配置文件

### 日常使用

启动开发服务器：

```bash
./start.sh
```

## 🔧 手动操作

### 创建虚拟环境

```bash
python3 -m venv venv
```

### 激活虚拟环境

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

激活后，你会看到命令行前面出现 `(venv)` 标识。

### 安装依赖

```bash
# 激活虚拟环境后
pip install -r requirements.txt
```

### 安装Playwright浏览器

```bash
playwright install chromium
```

### 退出虚拟环境

```bash
deactivate
```

## 📦 已安装的依赖

### 核心框架
- **FastAPI** (0.119.0): 高性能Web框架
- **Uvicorn** (0.37.0): ASGI服务器
- **Pydantic** (2.12.2): 数据验证和设置管理

### 爬虫相关
- **Playwright** (1.55.0): 浏览器自动化
- **playwright-stealth** (2.0.0): 反检测工具

### 数据处理
- **Pandas** (2.3.3): 数据分析库
- **OpenPyXL** (3.1.5): Excel文件处理
- **XlsxWriter** (3.2.9): Excel文件生成
- **NumPy** (2.3.4): 数值计算

### 其他依赖
- **HTTPX**: 异步HTTP客户端
- **Redis**: 缓存和任务队列
- **Loguru**: 日志记录
- **Requests**: HTTP请求库

## ⚙️ 配置文件

`.env` 文件包含所有配置项：

```env
# 应用配置
APP_NAME=SCZY数据报告系统
DEBUG=True
HOST=0.0.0.0
PORT=8000

# ERP系统配置
ERP_BASE_URL=https://your-erp-domain.com
ERP_USERNAME=your_username
ERP_PASSWORD=your_password

# 浏览器配置
BROWSER_HEADLESS=True
BROWSER_TIMEOUT=30000
```

## 🔍 环境验证

### 验证依赖导入

```bash
source venv/bin/activate
python -c "
import fastapi, uvicorn, playwright, pandas, openpyxl
print('✅ 所有依赖正常')
"
```

### 验证应用启动

```bash
source venv/bin/activate
python -c "
from app.main import app
print(f'✅ 应用正常: {app.title}')
"
```

### 验证Playwright

```bash
source venv/bin/activate
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        print('✅ Playwright正常')
        await browser.close()

asyncio.run(test())
"
```

## 🗂️ 项目目录

系统会自动创建以下目录：

- `logs/`: 日志文件
- `uploads/`: 上传文件
- `downloads/`: 下载文件
- `outputs/`: 输出文件
- `temp/`: 临时文件

## 🐛 常见问题

### 1. 虚拟环境激活失败

**问题**: `source venv/bin/activate` 命令失败

**解决方案**:
- 确认你在项目根目录
- 检查 `venv` 目录是否存在
- 重新创建虚拟环境

### 2. 依赖安装失败

**问题**: `pip install` 失败

**解决方案**:
- 升级pip: `pip install --upgrade pip`
- 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/`
- 检查Python版本兼容性

### 3. Playwright安装失败

**问题**: 浏览器下载失败

**解决方案**:
- 检查网络连接
- 使用代理: `PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net playwright install chromium`
- 手动下载浏览器

### 4. 配置文件错误

**问题**: `ImportError: No module named 'app.config.settings'`

**解决方案**:
- 检查 `.env` 文件是否存在
- 确认配置项格式正确
- 检查环境变量 `PYTHONPATH`

## 🔄 环境重置

如果遇到问题需要重置环境：

```bash
# 1. 删除虚拟环境
rm -rf venv/

# 2. 重新创建
./setup.sh
```

## 📝 开发建议

1. **保持环境干净**: 只在虚拟环境中安装依赖
2. **定期更新**: 定期更新依赖到最新版本
3. **版本锁定**: 生产环境使用具体版本号
4. **文档同步**: 更新依赖时同步更新文档

## 🔗 相关链接

- [Python虚拟环境文档](https://docs.python.org/3/library/venv.html)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Playwright官方文档](https://playwright.dev/python/)
- [Pandas官方文档](https://pandas.pydata.org/)

---

*最后更新: 2024-01-XX*