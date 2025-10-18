# 爬虫工具模块

这个目录包含专门为爬虫功能设计的通用工具和辅助函数。

## 模块列表

### task_center.py
任务中心工具模块，用于处理ERP系统中的大文件导出任务。

**主要功能:**
- 智能打开任务中心抽屉（自动弹出检测 + 手动点击）
- 双重监听方案（API接口监听 + 页面元素监听）
- 文件下载和自定义命名
- 完善的错误处理和日志记录

**使用方式:**
```python
from app.crawlers.utils import wait_for_export_task

# 基本使用
download_path = await wait_for_export_task(page=page)

# 自定义文件名和超时
download_path = await wait_for_export_task(
    page=page,
    filename="导出文件名",
    timeout=300
)
```

**适用场景:**
- 商品档案导出
- 订单数据导出
- 库存数据导出
- 其他需要通过任务中心处理的大文件导出

## 设计原则

1. **模块化**: 每个工具专注于特定功能领域
2. **可复用**: 设计为通用的接口，可在多个爬虫中使用
3. **健壮性**: 完善的错误处理和多重备用方案
4. **易维护**: 清晰的代码结构和详细的文档说明