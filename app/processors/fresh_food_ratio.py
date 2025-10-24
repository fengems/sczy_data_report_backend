"""
生鲜环比处理模块 - 重构后的入口文件
此文件保持向后兼容性，内部使用重构后的模块化代码
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Tuple, Optional, Union

# 导入重构后的模块
from app.processors.fresh_food_ratio.service import FreshFoodRatioService as _FreshFoodRatioService
from app.processors.fresh_food_ratio.main import process_fresh_food_ratio as _process_fresh_food_ratio
from app.processors.fresh_food_ratio.main import 函数 as _函数

logger = logging.getLogger(__name__)

# 为了向后兼容，重新导出所有必要的类和函数
FreshFoodRatioService = _FreshFoodRatioService

# 从新模块导出处理器和写入器
from app.processors.fresh_food_ratio.processor import FreshFoodRatioProcessor
from app.outputs.fresh_food_ratio.writer import FreshFoodRatioExcelWriter as ExcelReportWriter

# 便捷函数
def process_fresh_food_ratio(
    last_month_order_file: str,
    this_month_order_file: str,
    output_file: Optional[str] = None
) -> Tuple[pd.DataFrame, str]:
    """
    处理生鲜环比数据的便捷函数

    Args:
        last_month_order_file: 上个月订单数据的Excel文件地址
        this_month_order_file: 本月订单数据的Excel文件地址
        output_file: 输出文件路径

    Returns:
        Tuple[客户环比数据DataFrame, 输出文件路径]
    """
    return _process_fresh_food_ratio(last_month_order_file, this_month_order_file, output_file)


# 中文函数名，保持向后兼容
def 函数(lastMonthOrderFile: str, thisMonthOrderFile: str) -> Tuple[pd.DataFrame, str]:
    """
    中文命名的便捷函数，仅支持必需参数

    Args:
        lastMonthOrderFile: 上个月的订单数据的 excel 文件地址
        thisMonthOrderFile: 本月的订单数据的 excel 文件地址

    Returns:
        Tuple[客户环比数据DataFrame, 输出文件路径]
    """
    return _函数(lastMonthOrderFile, thisMonthOrderFile)