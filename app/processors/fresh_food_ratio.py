"""
生鲜环比业务处理模块
整合数据处理和输出生成的完整业务流程
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Tuple

from .excel_processor import FreshFoodRatioProcessor, get_customer_diff
from ..outputs.excel_writer import ExcelReportWriter, generate_fresh_food_ratio_report

logger = logging.getLogger(__name__)


class FreshFoodRatioService:
    """生鲜环比业务服务"""

    def __init__(self):
        """初始化服务"""
        self.processor = FreshFoodRatioProcessor()
        self.writer = ExcelReportWriter()

    def process_fresh_food_ratio(
        self,
        last_month_order_file: str,
        this_month_order_file: str,
        output_file: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        处理生鲜环比数据的完整流程

        Args:
            last_month_order_file: 上个月订单数据的Excel文件地址
            this_month_order_file: 本月订单数据的Excel文件地址
            output_file: 输出文件路径，如果为None则自动生成

        Returns:
            Tuple[客户环比数据DataFrame, 输出文件路径]
        """
        logger.info("开始生鲜环比数据处理流程...")

        try:
            # 1. 验证输入文件
            self._validate_input_files(last_month_order_file, this_month_order_file)

            # 2. 处理客户环比数据
            logger.info("正在处理客户环比数据...")
            customer_diff_df = self.processor.get_customer_diff(
                last_month_order_file,
                this_month_order_file
            )

            # 3. 生成Excel报告
            logger.info("正在生成Excel报告...")
            output_path = self.writer.write_fresh_food_ratio_report(
                customer_diff_df,
                output_file
            )

            logger.info("生鲜环比数据处理流程完成")
            return customer_diff_df, output_path

        except Exception as e:
            logger.error(f"生鲜环比数据处理失败: {str(e)}")
            raise

    def _validate_input_files(self, last_month_file: str, this_month_file: str):
        """
        验证输入文件是否存在

        Args:
            last_month_file: 上个月文件路径
            this_month_file: 本月文件路径
        """
        last_path = Path(last_month_file)
        this_path = Path(this_month_file)

        if not last_path.exists():
            raise FileNotFoundError(f"上个月订单文件不存在: {last_month_file}")

        if not this_path.exists():
            raise FileNotFoundError(f"本月订单文件不存在: {this_month_file}")

        if not str(last_path).lower().endswith(('.xlsx', '.xls')):
            raise ValueError(f"上个月文件格式不支持: {last_month_file}")

        if not str(this_path).lower().endswith(('.xlsx', '.xls')):
            raise ValueError(f"本月文件格式不支持: {this_month_file}")

        logger.info("输入文件验证通过")


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
    service = FreshFoodRatioService()
    return service.process_fresh_food_ratio(
        last_month_order_file,
        this_month_order_file,
        output_file
    )


# 便捷函数，符合伪代码中的函数名
def 函数(lastMonthOrderFile: str, thisMonthOrderFile: str) -> Tuple[pd.DataFrame, str]:
    """
    生鲜环比处理主函数

    Args:
        lastMonthOrderFile: 上个月的订单数据的 excel 文件地址
        thisMonthOrderFile: 本月的订单数据的 excel 文件地址

    Returns:
        Tuple[客户环比数据DataFrame, 输出文件路径]
    """
    return process_fresh_food_ratio(lastMonthOrderFile, thisMonthOrderFile)