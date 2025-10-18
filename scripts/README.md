# Scripts 目录

这个目录包含用于运行和测试爬虫功能的脚本。

## 脚本列表

### 1. run_goods_archive_crawler.py
商品档案爬虫的快速运行脚本。

**使用方法:**
```bash
cd scripts
python run_goods_archive_crawler.py
```

**功能:**
- 自动登录ERP系统
- 导航到商品档案页面
- 自动执行导出流程
- 下载商品档案Excel文件

**说明:**
- 脚本会处理所有页面交互：filter定位、导出按钮hover、dropdown选择、modal确认等
- 详细的日志输出会在控制台显示
- 下载的文件会保存到项目的 `downloads/` 目录
- 如果出现错误，会自动截图保存到 `temp/` 目录用于调试

## 依赖要求

确保在项目根目录下有正确的 `.env` 配置文件，包含：
- `erp_base_url`: ERP系统基础URL
- `erp_username`: ERP用户名
- `erp_password`: ERP密码

## 注意事项

- 运行脚本前请确保已激活Python虚拟环境
- 脚本需要Chrome浏览器支持
- 首次运行可能需要下载Playwright的浏览器驱动
- 请确保网络连接正常，能够访问ERP系统