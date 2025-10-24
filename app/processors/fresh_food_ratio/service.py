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
                               output_file: Optional[Union[str, Path]] = None) -> Tuple[pd.DataFrame, str]:
        """
        处理生鲜环比数据并生成Excel报告

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径
            output_file: 输出文件路径，如果为None则自动生成

        Returns:
            tuple: (处理结果DataFrame, 输出文件路径)

        Raises:
            FileNotFoundError: 输入文件不存在
            ValueError: 文件格式错误或数据处理失败
        """
        try:
            # 验证输入文件
            self._validate_input_files(last_month_file, this_month_file)

            # 处理数据
            logger.info("开始处理生鲜环比数据...")
            result_df = self.processor.get_customer_diff(last_month_file, this_month_file)

            # 生成Excel报告
            logger.info("开始生成Excel报告...")
            result_path = self.writer.write_report(result_df, output_file)

            logger.info(f"生鲜环比处理完成，输出文件: {result_path}")
            return result_df, result_path

        except Exception as e:
            logger.error(f"生鲜环比处理失败: {str(e)}")
            raise