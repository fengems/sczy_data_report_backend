"""
生鲜环比处理模块
提供生鲜环比数据处理的所有功能
"""

from .processor import FreshFoodRatioProcessor
from .service import FreshFoodRatioService
from .main import process_fresh_food_ratio, 函数

# 为了向后兼容，从输出模块导入
from app.outputs.fresh_food_ratio.writer import FreshFoodRatioExcelWriter

# 向后兼容的别名
ExcelReportWriter = FreshFoodRatioExcelWriter

__all__ = [
    'FreshFoodRatioProcessor',
    'FreshFoodRatioService',
    'process_fresh_food_ratio',
    '函数',
    'FreshFoodRatioExcelWriter',
    'ExcelReportWriter'
]
