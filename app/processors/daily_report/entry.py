"""
日报数据处理模块入口
提供便捷的接口供外部调用
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from .service import DailyReportService

logger = logging.getLogger(__name__)


# 创建全局服务实例
_daily_report_service = None


def get_daily_report_service(output_dir: Optional[Union[str, Path]] = None) -> DailyReportService:
    """
    获取日报服务实例

    Args:
        output_dir: 输出目录

    Returns:
        DailyReportService: 服务实例
    """
    global _daily_report_service
    if _daily_report_service is None:
        _daily_report_service = DailyReportService(output_dir)
    return _daily_report_service


def generate_daily_report(current_excel: str, compare_excel: str,
                         extra_compare_excel: Optional[str] = None,
                         output_file: Optional[Union[str, Path]] = None) -> str:
    """
    生成完整的日报报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_file: 输出文件路径

    Returns:
        str: 生成的文件路径
    """
    service = get_daily_report_service()
    return service.generate_daily_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel,
        output_file=output_file
    )


def generate_category_report(current_excel: str, compare_excel: str,
                           extra_compare_excel: Optional[str] = None,
                           output_file: Optional[Union[str, Path]] = None) -> str:
    """
    生成品类数据报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_file: 输出文件路径

    Returns:
        str: 生成的文件路径
    """
    service = get_daily_report_service()
    return service.generate_single_sheet_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel,
        sheet_name="品类数据",
        row_fields=['一级分类'],
        filter_options=[],
        output_file=output_file
    )


def generate_sales_report(current_excel: str, compare_excel: str,
                         extra_compare_excel: Optional[str] = None,
                         output_file: Optional[Union[str, Path]] = None) -> str:
    """
    生成业务数据报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_file: 输出文件路径

    Returns:
        str: 生成的文件路径
    """
    service = get_daily_report_service()
    return service.generate_single_sheet_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel,
        sheet_name="业务数据",
        row_fields=['业务员'],
        filter_options=[],
        output_file=output_file
    )


def generate_vegetable_report(current_excel: str, compare_excel: str,
                            extra_compare_excel: Optional[str] = None,
                            output_file: Optional[Union[str, Path]] = None) -> str:
    """
    生成业务蔬菜数据报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_file: 输出文件路径

    Returns:
        str: 生成的文件路径
    """
    service = get_daily_report_service()
    return service.generate_single_sheet_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel,
        sheet_name="业务蔬菜数据",
        row_fields=['业务员'],
        filter_options=[{'key': '一级分类', 'value': ['新鲜蔬菜'], 'reverse': False}],
        output_file=output_file
    )


def generate_route_report(current_excel: str, compare_excel: str,
                         extra_compare_excel: Optional[str] = None,
                         output_file: Optional[Union[str, Path]] = None) -> str:
    """
    生成线路数据报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_file: 输出文件路径

    Returns:
        str: 生成的文件路径
    """
    service = get_daily_report_service()
    return service.generate_single_sheet_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel,
        sheet_name="线路数据",
        row_fields=['线路名称'],
        filter_options=[],
        output_file=output_file
    )


def generate_route_category_report(current_excel: str, compare_excel: str,
                                 extra_compare_excel: Optional[str] = None,
                                 output_file: Optional[Union[str, Path]] = None) -> str:
    """
    生成线路品类报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_file: 输出文件路径

    Returns:
        str: 生成的文件路径
    """
    service = get_daily_report_service()
    return service.generate_single_sheet_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel,
        sheet_name="线路品类",
        row_fields=['线路名称', '一级分类'],
        filter_options=[],
        output_file=output_file
    )


# 批量生成所有报告
def generate_all_reports(current_excel: str, compare_excel: str,
                        extra_compare_excel: Optional[str] = None,
                        output_dir: Optional[Union[str, Path]] = None) -> List[str]:
    """
    批量生成所有日报报告

    Args:
        current_excel: 当前Excel文件路径
        compare_excel: 对比Excel文件路径
        extra_compare_excel: 额外对比Excel文件路径
        output_dir: 输出目录

    Returns:
        List[str]: 生成的文件路径列表
    """
    service = get_daily_report_service(output_dir)

    # 生成完整报告
    full_report = service.generate_daily_report(
        current_excel=current_excel,
        compare_excel=compare_excel,
        extra_compare_excel=extra_compare_excel
    )

    # 生成各个单独报告
    reports = [full_report]

    return reports