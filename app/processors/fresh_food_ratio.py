"""
生鲜环比处理模块 - 向后兼容入口
此文件提供向后兼容的导入路径，内部使用重构后的模块化代码
"""

# 为了向后兼容，重新导出所有必要的类和函数
from .fresh_food_ratio.entry import (
    FreshFoodRatioService,
    FreshFoodRatioProcessor,
    ExcelReportWriter,
    process_fresh_food_ratio,
    函数
)

# 重新导出，确保原有的导入路径继续有效
__all__ = [
    'FreshFoodRatioService',
    'FreshFoodRatioProcessor',
    'ExcelReportWriter',
    'process_fresh_food_ratio',
    '函数'
]