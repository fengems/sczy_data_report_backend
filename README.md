# SCZY ERP数据爬取系统

一个基于FastAPI和Playwright的ERP数据爬取和处理系统，支持自动化数据获取、Excel处理和企业微信推送。

## 功能特性

- 🚀 **自动化爬虫**: 基于Playwright的稳定网页自动化
- 📊 **数据处理**: 支持Excel数据的清洗、转换和格式化
- 📱 **企业微信集成**: 自动推送处理结果到企业微信群
- 🔄 **异步任务**: 基于Celery的任务队列系统
- 📝 **完整文档**: 自动生成的API文档
- 🛡️ **错误处理**: 完善的异常处理和日志记录

## 技术栈

- **后端框架**: FastAPI
- **爬虫引擎**: Playwright
- **数据处理**: Pandas + openpyxl + XlsxWriter
- **任务队列**: Celery + Redis
- **配置管理**: Pydantic Settings
- **日志系统**: loguru + structlog

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/fengems/sczy_data_report_backend.git
cd sczy_data_report_backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install
```

### 2. 配置设置

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑配置文件，填入你的ERP系统信息
vim .env
```

主要配置项：
```env
# ERP系统配置
ERP_BASE_URL=https://your-erp-domain.com
ERP_USERNAME=your_username
ERP_PASSWORD=your_password

# 企业微信配置
WECHAT_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_webhook_key
```

### 3. 启动服务

```bash
# 启动FastAPI服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery worker (新终端)
celery -A tasks worker --loglevel=info

# 启动Celery beat (定时任务，新终端)
celery -A tasks beat --loglevel=info
```

### 4. 访问服务

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health
- **系统状态**: http://localhost:8000/api/v1/ping

## 项目结构

```
sczy_data_report_backend/
├── app/
│   ├── api/              # API路由
│   │   ├── health.py     # 健康检查
│   │   └── crawler.py    # 爬虫管理
│   ├── crawlers/         # 爬虫模块
│   │   ├── base.py       # 基础爬虫类
│   │   ├── auth.py       # 登录认证
│   │   └── modules/      # 业务爬虫模块
│   ├── processors/       # 数据处理
│   ├── outputs/          # 输出处理
│   ├── models/           # 数据模型
│   ├── utils/            # 工具函数
│   │   └── logger.py     # 日志配置
│   ├── config/           # 配置管理
│   │   └── settings.py   # 应用配置
│   └── main.py           # FastAPI主应用
├── tasks/                # Celery任务
├── tests/                # 测试代码
├── docs/                 # 项目文档
│   ├── PLAN.md          # 项目规划
│   └── RESEARCH.md      # 技术选型
├── requirements.txt      # 依赖列表
├── .env.example         # 配置模板
└── README.md            # 项目说明
```

## API使用示例

### 1. 运行爬虫任务

```bash
curl -X POST "http://localhost:8000/api/v1/crawler/run" \
-H "Content-Type: application/json" \
-d '{
  "crawler_name": "sales_data",
  "params": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "output_format": "excel"
}'
```

### 2. 查询任务状态

```bash
curl "http://localhost:8000/api/v1/crawler/tasks/task_001"
```

### 3. 获取可用爬虫列表

```bash
curl "http://localhost:8000/api/v1/crawler/crawlers"
```

## 开发指南

### 创建新的爬虫模块

1. 继承`BaseCrawler`类
2. 实现`login()`和`crawl_data()`方法
3. 在`app/crawlers/modules/`目录下创建文件

示例：
```python
from app.crawlers.base import BaseCrawler
from typing import Dict, Any

class SalesDataCrawler(BaseCrawler):
    def __init__(self):
        super().__init__("sales_data")

    async def login(self) -> bool:
        # 实现登录逻辑
        return True

    async def crawl_data(self, params: Dict[str, Any]) -> str:
        # 实现数据爬取逻辑
        return "data_file_path"
```

### 添加数据处理逻辑

在`app/processors/`目录下创建数据处理模块，使用pandas进行数据清洗和转换。

### 配置企业微信推送

在`app/outputs/`目录下实现企业微信推送逻辑，支持文件和消息推送。

## 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t sczy-crawler .

# 运行容器
docker run -d \
  --name sczy-crawler \
  -p 8000:8000 \
  --env-file .env \
  sczy-crawler
```

### 生产环境注意事项

1. **安全配置**: 修改默认密码，配置HTTPS
2. **性能优化**: 调整worker数量和内存限制
3. **监控告警**: 配置日志监控和告警机制
4. **备份策略**: 定期备份数据和配置文件

## 故障排除

### 常见问题

1. **Playwright安装失败**
   ```bash
   # 手动安装浏览器
   playwright install chromium
   ```

2. **登录失败**
   - 检查ERP系统URL是否正确
   - 确认用户名密码无误
   - 查看是否有验证码或二次认证

3. **任务执行失败**
   - 检查日志文件了解具体错误
   - 确认网络连接正常
   - 验证目标页面结构是否发生变化

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Celery日志
tail -f logs/celery.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系项目维护者。