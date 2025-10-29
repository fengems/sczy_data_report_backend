"""
生鲜环比服务
整合生鲜环比的处理器和写入器，提供业务接口
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Tuple, Optional, Union

from app.processors.fresh_food_ratio.processor import FreshFoodRatioProcessor
from app.outputs.fresh_food_ratio.writer import FreshFoodRatioExcelWriter

logger = logging.getLogger(__name__)


class FreshFoodRatioService:
    """生鲜环比服务"""

    def __init__(self):
        """初始化服务"""
        self.processor = FreshFoodRatioProcessor()
        self.writer = FreshFoodRatioExcelWriter()

    def _validate_input_files(self, last_month_file: str, this_month_file: str):
        """
        验证输入文件

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        last_path = Path(last_month_file)
        this_path = Path(this_month_file)

        if not last_path.exists():
            raise FileNotFoundError(f"上月数据文件不存在: {last_month_file}")
        if not this_path.exists():
            raise FileNotFoundError(f"本月数据文件不存在: {this_month_file}")

        # 检查文件格式
        if last_path.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError(f"上月数据文件格式不支持: {last_month_file}")
        if this_path.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError(f"本月数据文件格式不支持: {this_month_file}")

        logger.info("输入文件验证通过")

    def process_fresh_food_ratio(self, last_month_file: str, this_month_file: str,
                               output_file: Optional[Union[str, Path]] = None,
                               include_region_ratio: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        处理生鲜环比数据并生成Excel报告（支持客户环比和区域环比）

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径
            output_file: 输出文件路径，如果为None则自动生成
            include_region_ratio: 是否包含区域环比分析

        Returns:
            tuple: (处理结果DataFrame, 输出文件路径)

        Raises:
            FileNotFoundError: 输入文件不存在
            ValueError: 文件格式错误或数据处理失败
        """
        try:
            # 验证输入文件
            self._validate_input_files(last_month_file, this_month_file)

            # 处理客户环比数据
            logger.info("开始处理客户环比数据...")
            customer_result_df = self.processor.get_customer_diff(last_month_file, this_month_file)

            # 处理区域环比数据（如果启用）
            region_result_df = None
            if include_region_ratio:
                try:
                    logger.info("开始处理区域环比数据...")
                    region_result_df = self.processor.get_region_diff(last_month_file, this_month_file)
                    logger.info("区域环比数据处理完成")
                except Exception as e:
                    logger.warning(f"区域环比数据处理失败，将只生成客户环比报告: {str(e)}")
                    # 继续处理，但不包含区域环比

            # 生成Excel报告
            logger.info("开始生成Excel报告...")
            result_path = self.writer.write_report(customer_result_df, region_result_df, output_file)

            logger.info(f"生鲜环比处理完成，输出文件: {result_path}")
            return customer_result_df, result_path

        except Exception as e:
            logger.error(f"生鲜环比处理失败: {str(e)}")
            raise

    def process_customer_ratio_only(self, last_month_file: str, this_month_file: str,
                                   output_file: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, str]:
        """
        仅处理客户环比数据（保持向后兼容性）

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径
            output_file: 输出文件路径，如果为None则自动生成

        Returns:
            tuple: (处理结果DataFrame, 输出文件路径)
        """
        return self.process_fresh_food_ratio(last_month_file, this_month_file, output_file, include_region_ratio=False)

    def process_region_ratio_only(self, last_month_file: str, this_month_file: str,
                                 output_file: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, str]:
        """
        仅处理区域环比数据

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径
            output_file: 输出文件路径，如果为None则自动生成

        Returns:
            tuple: (区域环比结果DataFrame, 输出文件路径)
        """
        try:
            # 验证输入文件
            self._validate_input_files(last_month_file, this_month_file)

            # 处理区域环比数据
            logger.info("开始处理区域环比数据...")
            region_result_df = self.processor.get_region_diff(last_month_file, this_month_file)

            # 生成仅包含区域环比的Excel报告
            logger.info("开始生成区域环比Excel报告...")
            result_path = self.writer.write_report(pd.DataFrame(), region_result_df, output_file)

            logger.info(f"区域环比处理完成，输出文件: {result_path}")
            return region_result_df, result_path

        except Exception as e:
            logger.error(f"区域环比处理失败: {str(e)}")
            raise