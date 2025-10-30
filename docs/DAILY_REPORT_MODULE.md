# 日报数据处理模块文档

## 概述

日报数据处理模块是用于处理ERP系统中日报数据的专用模块，支持数据透视分析、多维度对比和专业的Excel报告生成。该模块于 **2025-10-30** 正式实现完成。

## 功能特性

### 核心功能
- **数据透视分析**: 支持按一级分类、业务员、线路名称等维度进行数据透视
- **多时期对比**: 支持当前时期与对比时期的数据对比分析
- **日报数据处理**: 自动计算日活（客户数量）和实际金额的平均值
- **环比计算**: 自动计算差值和环比百分比
- **专业Excel输出**: 生成格式化的Excel报告，包含条件格式化

### 报告类型
1. **品类数据报告**: 按商品一级分类维度分析
2. **业务数据报告**: 按业务员维度分析
3. **业务蔬菜数据报告**: 专门分析新鲜蔬菜类别的业务数据
4. **线路数据报告**: 按配送线路维度分析
5. **线路品类报告**: 按线路和商品分类交叉维度分析

## 模块架构

### 目录结构
```
app/processors/daily_report/
├── __init__.py              # 模块初始化
├── processor.py             # 核心数据处理器
├── service.py               # 服务层
└── entry.py                 # 对外接口入口

app/outputs/daily_report/
├── __init__.py              # 输出模块初始化
└── writer.py                # Excel写入器

examples/
└── daily_report_example.py  # 使用示例脚本
```

### 核心类设计

#### 1. DailyReportProcessor
**职责**: 数据处理和透视分析
- 继承自 `BaseExcelProcessor`
- 实现数据透视、对比分析、数据合并等核心逻辑
- 支持灵活的过滤和分组配置

#### 2. DailyReportWriter
**职责**: Excel格式化和输出
- 继承自 `BaseExcelWriter`
- 实现专业的Excel格式化，包括条件格式化、合并单元格等
- 支持多sheet输出和自定义样式

#### 3. DailyReportService
**职责**: 业务逻辑协调
- 协调Processor和Writer的工作
- 提供高级的业务接口
- 处理异常和日志记录

## 使用方法

### 1. 快速开始

```python
from app.processors.daily_report.entry import generate_daily_report

# 生成完整日报报告
report_path = generate_daily_report(
    current_excel="data/current_period.xlsx",
    compare_excel="data/compare_period.xlsx",
    extra_compare_excel="data/extra_compare_period.xlsx",  # 可选
    output_file="outputs/daily_report.xlsx"
)

print(f"报告已生成: {report_path}")
```

### 2. 生成特定类型报告

```python
from app.processors.daily_report.entry import (
    generate_category_report,
    generate_sales_report,
    generate_vegetable_report
)

# 生成品类数据报告
category_report = generate_category_report(
    current_excel="data/current.xlsx",
    compare_excel="data/compare.xlsx"
)

# 生成业务蔬菜数据报告
vegetable_report = generate_vegetable_report(
    current_excel="data/current.xlsx",
    compare_excel="data/compare.xlsx"
)
```

### 3. 使用服务层进行高级配置

```python
from app.processors.daily_report.service import DailyReportService

service = DailyReportService(output_dir="outputs/reports")

# 生成自定义sheet报告
output_path = service.generate_single_sheet_report(
    current_excel="data/current.xlsx",
    compare_excel="data/compare.xlsx",
    sheet_name="自定义报告",
    row_fields=['一级分类', '业务员'],  # 自定义行字段
    filter_options=[  # 自定义过滤条件
        {'key': '一级分类', 'value': ['新鲜蔬菜', '水果'], 'reverse': False}
    ]
)
```

## 数据格式要求

### 输入Excel文件格式
输入的Excel文件必须包含以下列：

| 列名 | 数据类型 | 说明 |
|------|----------|------|
| 客户名称 | 文本 | 客户名称或ID |
| 实际金额 | 数值 | 订单实际金额 |
| 发货时间 | 日期 | 发货日期 |
| 一级分类 | 文本 | 商品一级分类名称 |
| 业务员 | 文本 | 负责业务员姓名 |
| 线路名称 | 文本 | 配送线路名称 |

### 输出Excel文件格式
生成的Excel报告包含以下特征：

1. **合并标题行**: 每个sheet的第一行为合并的标题行
2. **条件格式化**: 负数自动显示为浅红填充深红色文本
3. **数据格式**: 金额列显示千分位，环比列显示百分比
4. **冻结窗格**: 冻结标题行便于浏览
5. **自动列宽**: 根据内容自动调整列宽

## API参考

### 核心接口函数

#### `generate_daily_report(current_excel, compare_excel, extra_compare_excel=None, output_file=None)`

生成完整的日报报告，包含所有sheet。

**参数:**
- `current_excel` (str): 当前时期Excel文件路径
- `compare_excel` (str): 对比时期Excel文件路径
- `extra_compare_excel` (str, 可选): 额外对比时期Excel文件路径
- `output_file` (str, 可选): 输出文件路径

**返回:**
- `str`: 生成的Excel文件路径

#### `generate_category_report(current_excel, compare_excel, extra_compare_excel=None, output_file=None)`

生成品类数据报告。

**参数和返回值同上。**

#### `generate_sales_report(current_excel, compare_excel, extra_compare_excel=None, output_file=None)`

生成业务数据报告。

#### `generate_vegetable_report(current_excel, compare_excel, extra_compare_excel=None, output_file=None)`

生成业务蔬菜数据报告（自动过滤新鲜蔬菜类别）。

## 运行示例

### 1. 运行示例脚本

```bash
cd /Users/fenge/code/sczy_data_report_backend
python examples/daily_report_example.py
```

### 2. 准备示例数据

在运行示例前，请确保以下文件存在：

```
data/
├── current_period.xlsx      # 当前时期数据
├── compare_period.xlsx      # 对比时期数据
└── extra_compare_period.xlsx # 额外对比数据（可选）
```

## 错误处理

### 常见错误及解决方案

1. **FileNotFoundError**: 输入Excel文件不存在
   - 检查文件路径是否正确
   - 确保文件具有读取权限

2. **ValueError**: Excel文件缺少必要的列
   - 检查输入文件是否包含所有必需的列
   - 确认列名拼写正确（注意空格）

3. **数据透视失败**: 数据为空或格式不正确
   - 检查数据是否包含有效的日期和数值
   - 确认过滤条件是否合理

## 性能优化

### 建议的数据量
- **推荐**: 单个文件不超过10万行数据
- **最大支持**: 单个文件不超过50万行数据

### 优化建议
1. 使用SSD存储提高文件读取速度
2. 确保足够的内存（建议8GB以上）
3. 定期清理临时文件

## 扩展开发

### 添加新的报告类型

1. 在 `processor.py` 中添加新的配置到 `sheets_config`
2. 在 `entry.py` 中添加对应的便捷函数
3. 更新文档和示例

### 自定义格式化

继承 `DailyReportWriter` 类并重写相关方法：

```python
class CustomDailyReportWriter(DailyReportWriter):
    def apply_custom_formatting(self, writer, sheet_name, sheet_data):
        # 实现自定义格式化逻辑
        pass
```

## 更新日志

### 2025-10-30 - v1.0.0
- ✅ 实现完整的日报数据处理模块
- ✅ 支持5种标准报告类型
- ✅ 实现专业的Excel格式化输出
- ✅ 提供完整的使用示例和文档
- ✅ 支持灵活的数据过滤和分组配置
- ✅ 实现条件格式化和自动列宽调整

## 维护说明

### 日常维护
- 定期检查日志输出，监控数据处理状态
- 根据业务需求调整过滤条件和分组逻辑
- 保持示例脚本的更新

### 故障排除
1. 查看日志文件获取详细错误信息
2. 验证输入数据格式是否符合要求
3. 检查输出目录权限和磁盘空间

---

**开发者**: AI Assistant
**最后更新**: 2025-10-30
**版本**: 1.0.0