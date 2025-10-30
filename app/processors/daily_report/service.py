"""
日报数据服务层
提供高级的日报数据处理服务
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from .processor import DailyReportProcessor
from ...outputs.daily_report.writer import DailyReportWriter

logger = logging.getLogger(__name__)


class DailyReportService:
    """日报数据服务类"""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """
        初始化日报服务

        Args:
            output_dir: 输出目录
        """
        self.processor = DailyReportProcessor()
        self.writer = DailyReportWriter(output_dir)

    def generate_daily_report(self, current_excel: str, compare_excel: str,
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

        Raises:
            FileNotFoundError: 输入文件不存在
            ValueError: 数据格式错误
        """
        try:
            logger.info("开始生成日报报告")

            # 验证输入文件
            if not Path(current_excel).exists():
                raise FileNotFoundError(f"当前Excel文件不存在: {current_excel}")
            if not Path(compare_excel).exists():
                raise FileNotFoundError(f"对比Excel文件不存在: {compare_excel}")
            if extra_compare_excel and not Path(extra_compare_excel).exists():
                raise FileNotFoundError(f"额外对比Excel文件不存在: {extra_compare_excel}")

            # 处理数据
            sheets_data = self.processor.process_daily_report(
                current_excel=current_excel,
                compare_excel=compare_excel,
                extra_compare_excel=extra_compare_excel
            )

            # 生成Excel文件
            output_path = self.writer.write_report(sheets_data, output_file)

            logger.info(f"日报报告生成完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"生成日报报告失败: {str(e)}")
            raise

    def generate_single_sheet_report(self, current_excel: str, compare_excel: str,
                                   extra_compare_excel: Optional[str] = None,
                                   sheet_name: str = "品类数据",
                                   row_fields: List[str] = None,
                                   filter_options: Optional[List[Dict[str, Any]]] = None,
                                   output_file: Optional[Union[str, Path]] = None) -> str:
        """
        生成单个sheet的报告

        Args:
            current_excel: 当前Excel文件路径
            compare_excel: 对比Excel文件路径
            extra_compare_excel: 额外对比Excel文件路径
            sheet_name: sheet名称
            row_fields: 行字段列表
            filter_options: 过滤选项
            output_file: 输出文件路径

        Returns:
            str: 生成的文件路径
        """
        try:
            logger.info(f"开始生成单个sheet报告: {sheet_name}")

            # 设置默认值
            if row_fields is None:
                row_fields = ['一级分类']
            if filter_options is None:
                filter_options = []

            # 读取数据
            current_data = self.processor.read_excel_file(current_excel)
            compare_data = self.processor.read_excel_file(compare_excel)
            extra_compare_data = None
            if extra_compare_excel:
                extra_compare_data = self.processor.read_excel_file(extra_compare_excel)

            # 数据预处理
            current_data = self.processor._preprocess_data(current_data)
            compare_data = self.processor._preprocess_data(compare_data)
            if extra_compare_data is not None:
                extra_compare_data = self.processor._preprocess_data(extra_compare_data)

            # 创建对比选项
            from .processor import CompareOptions
            options = CompareOptions(
                current_data=current_data,
                compare_data=compare_data,
                extra_compare_data=extra_compare_data,
                row_fields=row_fields,
                sheet_name=sheet_name,
                filter_options=filter_options
            )

            # 生成sheet数据
            sheet_data = self.processor.get_compare_sheet(options)

            # 生成Excel文件
            output_path = self.writer.write_single_sheet_report(sheet_data, output_file)

            logger.info(f"单个sheet报告生成完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"生成单个sheet报告失败: {str(e)}")
            raise