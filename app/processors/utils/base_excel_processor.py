"""
Excel处理基类
提供通用的Excel文件处理功能，所有具体的Excel处理器都应该继承这个基类
"""

import pandas as pd
import logging
from typing import List, Optional
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseExcelProcessor(ABC):
    """Excel处理器基类"""

    def __init__(self, required_columns: Optional[List[str]] = None):
        """
        初始化处理器

        Args:
            required_columns: 必需的列名列表，子类可以指定
        """
        self.required_columns = required_columns or []

    def validate_columns(self, df: pd.DataFrame, file_name: str) -> bool:
        """
        验证DataFrame是否包含必要的列

        Args:
            df: 要验证的DataFrame
            file_name: 文件名，用于日志

        Returns:
            bool: 验证是否通过
        """
        if not self.required_columns:
            return True

        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"文件 {file_name} 缺少必要的列: {missing_columns}")
            return False
        return True

    def read_excel_file(self, file_path: str, sheet_name: int = 0) -> pd.DataFrame:
        """
        读取Excel文件的通用方法

        Args:
            file_path: Excel文件路径
            sheet_name: 工作表索引或名称，默认为第一个工作表

        Returns:
            pd.DataFrame: 读取的数据

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或缺少必要列
        """
        try:
            logger.info(f"正在读取文件: {file_path}")

            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 读取Excel文件
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # 标准化列名（去除空格）
            df.columns = df.columns.str.strip()

            # 验证必要的列
            if not self.validate_columns(df, file_path):
                raise ValueError(f"文件 {file_path} 缺少必要的列")

            logger.info(f"成功读取文件 {file_path}，共 {len(df)} 行数据")
            return df

        except Exception as e:
            logger.error(f"读取Excel文件失败: {file_path}, 错误: {str(e)}")
            raise

    def clean_numeric_column(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """
        清理数值列，将字符串转换为数值

        Args:
            df: 要处理的DataFrame
            column_name: 列名

        Returns:
            pd.DataFrame: 处理后的DataFrame
        """
        if column_name in df.columns:
            df[column_name] = pd.to_numeric(df[column_name], errors='coerce').fillna(0)
            logger.info(f"已清理数值列: {column_name}")
        return df

    def clean_datetime_column(self, df: pd.DataFrame, column_name: str) -> pd.DataFrame:
        """
        清理日期时间列

        Args:
            df: 要处理的DataFrame
            column_name: 列名

        Returns:
            pd.DataFrame: 处理后的DataFrame
        """
        if column_name in df.columns:
            df[column_name] = pd.to_datetime(df[column_name])
            logger.info(f"已清理日期时间列: {column_name}")
        return df

    def filter_data(self, df: pd.DataFrame, conditions: dict) -> pd.DataFrame:
        """
        根据条件过滤数据

        Args:
            df: 要过滤的DataFrame
            conditions: 过滤条件字典，例如: {'column_name': 'value', 'another_column': lambda x: x > 0}

        Returns:
            pd.DataFrame: 过滤后的DataFrame
        """
        filtered_df = df.copy()

        for column, condition in conditions.items():
            if column not in filtered_df.columns:
                logger.warning(f"过滤条件中的列不存在: {column}")
                continue

            if callable(condition):
                # 如果条件是函数
                mask = filtered_df[column].apply(condition)
            else:
                # 如果条件是值
                mask = filtered_df[column] == condition

            filtered_df = filtered_df[mask]
            logger.info(f"应用过滤条件 {column}: 保留 {len(filtered_df)} 行数据")

        return filtered_df

    @abstractmethod
    def process(self, *args, **kwargs) -> pd.DataFrame:
        """
        抽象方法，子类必须实现具体的处理逻辑

        Returns:
            pd.DataFrame: 处理后的数据
        """
        pass