"""
生鲜环比处理主入口文件
提供便捷的函数接口，保持向后兼容性
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Tuple, Optional, Union

from .service import FreshFoodRatioService

logger = logging.getLogger(__name__)


def process_fresh_food_ratio(last_month_file: str, this_month_file: str,
                            output_file: Optional[Union[str, Path]] = None,
                            include_region_ratio: bool = True) -> Tuple[pd.DataFrame, str]:
    """
    处理生鲜环比数据的便捷函数（支持客户环比和区域环比）

    Args:
        last_month_file: 上月数据文件路径
        this_month_file: 本月数据文件路径
        output_file: 输出文件路径，如果为None则自动生成
        include_region_ratio: 是否包含区域环比分析

    Returns:
        tuple: (处理结果DataFrame, 输出文件路径)
    """
    service = FreshFoodRatioService()
    return service.process_fresh_food_ratio(last_month_file, this_month_file, output_file, include_region_ratio)


# 中文函数名，保持向后兼容
def 函数(last_month_file: str, this_month_file: str) -> Tuple[pd.DataFrame, str]:
    """
    中文命名的便捷函数，仅支持必需参数

    Args:
        last_month_file: 上月数据文件路径
        this_month_file: 本月数据文件路径

    Returns:
        tuple: (处理结果DataFrame, 输出文件路径)
    """
    return process_fresh_food_ratio(last_month_file, this_month_file)


# 区域环比专用函数
def process_region_ratio(last_month_file: str, this_month_file: str,
                        output_file: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, str]:
    """
    处理区域环比数据的便捷函数

    Args:
        last_month_file: 上月数据文件路径
        this_month_file: 本月数据文件路径
        output_file: 输出文件路径，如果为None则自动生成

    Returns:
        tuple: (区域环比结果DataFrame, 输出文件路径)
    """
    service = FreshFoodRatioService()
    return service.process_region_ratio_only(last_month_file, this_month_file, output_file)


def process_customer_ratio_only(last_month_file: str, this_month_file: str,
                               output_file: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, str]:
    """
    仅处理客户环比数据的便捷函数（保持向后兼容）

    Args:
        last_month_file: 上月数据文件路径
        this_month_file: 本月数据文件路径
        output_file: 输出文件路径，如果为None则自动生成

    Returns:
        tuple: (处理结果DataFrame, 输出文件路径)
    """
    service = FreshFoodRatioService()
    return service.process_customer_ratio_only(last_month_file, this_month_file, output_file)


# 向后兼容的类别名
FreshFoodRatioProcessor = FreshFoodRatioService
ExcelReportWriter = None  # 这个需要从输出模块导入