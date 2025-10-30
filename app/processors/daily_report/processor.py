"""
日报数据处理器
处理日报数据的透视分析和对比功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from pathlib import Path

from ..utils.base_excel_processor import BaseExcelProcessor

logger = logging.getLogger(__name__)


@dataclass
class CompareOptions:
    """对比选项配置"""
    current_data: pd.DataFrame
    compare_data: pd.DataFrame
    extra_compare_data: Optional[pd.DataFrame] = None
    row_fields: List[str] = None
    sheet_name: str = ""
    filter_options: List[Dict[str, Any]] = None


class DailyReportProcessor(BaseExcelProcessor):
    """日报数据处理器"""

    def __init__(self):
        """初始化日报数据处理器"""
        # 日报数据必需的列
        required_columns = [
            '客户名称', '实际金额', '发货时间',
            '一级分类', '业务员', '线路名称'
        ]
        super().__init__(required_columns)

    def process(self, *args, **kwargs) -> Dict[str, Any]:
        """
        处理日报数据的主要入口

        Args:
            current_excel: 当前Excel文件路径
            compare_excel: 对比Excel文件路径
            extra_compare_excel: 额外对比Excel文件路径

        Returns:
            Dict[str, Any]: 处理结果数据
        """
        current_excel = kwargs.get('current_excel')
        compare_excel = kwargs.get('compare_excel')
        extra_compare_excel = kwargs.get('extra_compare_excel')

        # 读取数据
        current_data = self.read_excel_file(current_excel)
        compare_data = self.read_excel_file(compare_excel)
        extra_compare_data = None
        if extra_compare_excel:
            extra_compare_data = self.read_excel_file(extra_compare_excel)

        # 数据预处理
        current_data = self._preprocess_data(current_data)
        compare_data = self._preprocess_data(compare_data)
        if extra_compare_data is not None:
            extra_compare_data = self._preprocess_data(extra_compare_data)

        result = {
            'current_data': current_data,
            'compare_data': compare_data,
            'extra_compare_data': extra_compare_data
        }

        logger.info("日报数据处理完成")
        return result

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理

        Args:
            df: 原始数据

        Returns:
            pd.DataFrame: 预处理后的数据
        """
        # 清理数据
        df = df.copy()

        # 清理数值列
        df = self.clean_numeric_column(df, '实际金额')

        # 清理日期列
        df = self.clean_datetime_column(df, '发货时间')

        # 移除空行
        df = df.dropna(subset=['客户名称', '发货时间'])

        logger.info(f"数据预处理完成，保留 {len(df)} 行数据")
        return df

    def pivot_data(self, data: pd.DataFrame, row_fields: List[str]) -> Dict[str, pd.DataFrame]:
        """
        获取日活和实际金额的透视值

        Args:
            data: 原始数据
            row_fields: 透视行字段

        Returns:
            Dict[str, pd.DataFrame]: 包含日活和金额透视结果的字典
        """
        if data.empty:
            return {'daily_active': pd.DataFrame(), 'real_money': pd.DataFrame()}

        # 日活值透视 - 计算客户数量的平均值
        daily_active = data.pivot_table(
            index=row_fields,
            columns='发货时间',
            values='客户名称',
            aggfunc='nunique',  # 去重计数
            fill_value=0
        )

        # 如果有多列，计算平均值
        if len(daily_active.columns) > 1:
            daily_active['平均值'] = daily_active.mean(axis=1).round(2)  # 日活保留两位小数
        else:
            daily_active['平均值'] = daily_active.iloc[:, 0].round(2)  # 日活保留两位小数

        # 金额透视 - 计算金额的平均值
        real_money = data.pivot_table(
            index=row_fields,
            columns='发货时间',
            values='实际金额',
            aggfunc='sum',
            fill_value=0
        )

        # 如果有多列，计算平均值
        if len(real_money.columns) > 1:
            real_money['平均值'] = real_money.mean(axis=1).round(2)
        else:
            real_money['平均值'] = real_money.iloc[:, 0].round(2)

        logger.info(f"透视数据完成 - 日活: {daily_active.shape}, 金额: {real_money.shape}")
        return {'daily_active': daily_active, 'real_money': real_money}

    def filter_data_by_options(self, data: pd.DataFrame,
                             filter_options: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        根据过滤选项过滤数据

        Args:
            data: 原始数据
            filter_options: 过滤选项列表

        Returns:
            pd.DataFrame: 过滤后的数据
        """
        if not filter_options:
            return data

        filtered_data = data.copy()

        for option in filter_options:
            key = option.get('key')
            values = option.get('value', [])
            reverse = option.get('reverse', False)

            if key not in filtered_data.columns:
                logger.warning(f"过滤键不存在: {key}")
                continue

            if reverse:
                # 反向过滤 - 排除指定值
                filtered_data = filtered_data[~filtered_data[key].isin(values)]
            else:
                # 正向过滤 - 只包含指定值
                filtered_data = filtered_data[filtered_data[key].isin(values)]

            logger.info(f"应用过滤条件 {key}: 保留 {len(filtered_data)} 行数据")

        return filtered_data

    def get_date_range_description(self, data: pd.DataFrame, date_column: str = '发货时间') -> str:
        """
        获取数据范围的描述

        Args:
            data: 数据
            date_column: 日期列名

        Returns:
            str: 日期范围描述
        """
        if data.empty or date_column not in data.columns:
            return ""

        dates = pd.to_datetime(data[date_column]).dt.date
        min_date = dates.min()
        max_date = dates.max()

        if min_date == max_date:
            # 单日数据
            return f"{min_date.day}日"
        else:
            # 多日数据
            if min_date.month == max_date.month:
                return f"{min_date.month:02d}.{min_date.day:02d}-{max_date.day:02d}"
            else:
                return f"{min_date.month:02d}.{min_date.day:02d}-{max_date.month:02d}.{max_date.day:02d}"

    def collection_fields(self, pivot_data_list: List[Dict[str, pd.DataFrame]],
                         row_fields: List[str]) -> pd.DataFrame:
        """
        获取所有数据中的rowFields合集

        Args:
            pivot_data_list: 透视数据列表
            row_fields: 行字段列表

        Returns:
            pd.DataFrame: 合并后的行字段数据
        """
        all_indexes = []

        for pivot_data in pivot_data_list:
            if not pivot_data:
                continue

            daily_active = pivot_data.get('daily_active')
            real_money = pivot_data.get('real_money')

            if daily_active is not None and not daily_active.empty:
                all_indexes.append(daily_active.index)
            if real_money is not None and not real_money.empty:
                all_indexes.append(real_money.index)

        if not all_indexes:
            # 如果没有数据，创建空的DataFrame
            return pd.DataFrame(columns=row_fields)

        # 合并所有索引
        combined_index = all_indexes[0]
        for idx in all_indexes[1:]:
            combined_index = combined_index.union(idx)

        # 转换为DataFrame
        if isinstance(combined_index, pd.MultiIndex):
            result_df = pd.DataFrame(index=combined_index,
                                   columns=row_fields).reset_index(drop=True)
            # 重新填充行字段值
            for i, level_values in enumerate(combined_index):
                for j, field in enumerate(row_fields):
                    if j < len(level_values) if isinstance(level_values, tuple) else 1:
                        value = level_values[j] if isinstance(level_values, tuple) else level_values
                        result_df.iloc[i, j] = value
        else:
            result_df = pd.DataFrame({row_fields[0]: combined_index})

        logger.info(f"合并行字段完成，共 {len(result_df)} 行")
        return result_df

    def get_compare_data(self, row_fields_data: pd.DataFrame,
                        pivot_data_list: List[Dict[str, pd.DataFrame]]) -> pd.DataFrame:
        """
        生成对比数据

        Args:
            row_fields_data: 行字段数据
            pivot_data_list: 透视数据列表

        Returns:
            pd.DataFrame: 对比结果数据
        """
        result_df = row_fields_data.copy()

        # 数据列标题生成
        column_names = []
        data_values = []
        date_descriptions = []

        # 为每个数据集生成日活和金额列
        for i, pivot_data in enumerate(pivot_data_list):
            if not pivot_data:
                continue

            daily_active = pivot_data.get('daily_active', pd.DataFrame())
            real_money = pivot_data.get('real_money', pd.DataFrame())

            # 获取日期范围描述
            date_desc = self.get_date_range_description(self.current_data if i == 0 else
                                                       (self.compare_data if i == 1 else
                                                        self.extra_compare_data))
            date_descriptions.append(date_desc)

            # 添加日活列
            if not daily_active.empty:
                daily_active_col = []
                for _, row in row_fields_data.iterrows():
                    # 根据行字段值查找对应的日活数据
                    key_values = tuple(row[field] for field in daily_active.index.names if field in row)
                    if len(daily_active.index.names) == 1:
                        key_values = key_values[0] if key_values else None

                    if key_values in daily_active.index:
                        daily_active_col.append(daily_active.loc[key_values, '平均值'])
                    else:
                        daily_active_col.append(0)

                column_names.append(f"{date_desc}日活")
                data_values.append(daily_active_col)

            # 添加金额列
            if not real_money.empty:
                real_money_col = []
                for _, row in row_fields_data.iterrows():
                    # 根据行字段值查找对应的金额数据
                    key_values = tuple(row[field] for field in real_money.index.names if field in row)
                    if len(real_money.index.names) == 1:
                        key_values = key_values[0] if key_values else None

                    if key_values in real_money.index:
                        real_money_col.append(real_money.loc[key_values, '平均值'])
                    else:
                        real_money_col.append(0)

                column_names.append(f"{date_desc}金额")
                data_values.append(real_money_col)

        # 将数据列添加到结果DataFrame
        for i, col_name in enumerate(column_names):
            result_df[col_name] = data_values[i]

        # 计算差值和环比列
        if len(data_values) >= 2:
            # 分离日活列和金额列
            daily_active_cols = [col for col in column_names if '日活' in col]
            real_money_cols = [col for col in column_names if '金额' in col]

            # 计算日活差值和环比 - 与对比期的对比
            if len(daily_active_cols) >= 1:
                current_col = daily_active_cols[0]  # 当前期

                # 与对比期对比
                if len(daily_active_cols) >= 2:
                    compare_col = daily_active_cols[1]
                    compare_desc = date_descriptions[1]

                    # 差值列
                    diff_col = f"对比{compare_desc}日活差值"
                    result_df[diff_col] = result_df[current_col] - result_df[compare_col]

                    # 环比列 - 处理除零情况
                    ratio_col = f"对比{compare_desc}日活环比"
                    # 避免除零错误：当分母为0时，环比显示为空
                    with np.errstate(divide='ignore', invalid='ignore'):
                        ratio_values = (result_df[current_col] / result_df[compare_col] - 1)
                        ratio_values[result_df[compare_col] == 0] = np.nan  # 分母为0时设为NaN
                        result_df[ratio_col] = ratio_values.round(4)  # 保留4位小数，Excel百分比格式会显示为2位

                # 与额外对比期对比
                if len(daily_active_cols) >= 3:
                    extra_compare_col = daily_active_cols[2]
                    extra_compare_desc = date_descriptions[2]

                    # 差值列
                    diff_col = f"对比{extra_compare_desc}日活差值"
                    result_df[diff_col] = result_df[current_col] - result_df[extra_compare_col]

                    # 环比列 - 处理除零情况
                    ratio_col = f"对比{extra_compare_desc}日活环比"
                    # 避免除零错误：当分母为0时，环比显示为空
                    with np.errstate(divide='ignore', invalid='ignore'):
                        ratio_values = (result_df[current_col] / result_df[extra_compare_col] - 1)
                        ratio_values[result_df[extra_compare_col] == 0] = np.nan  # 分母为0时设为NaN
                        result_df[ratio_col] = ratio_values.round(4)  # 保留4位小数，Excel百分比格式会显示为2位

            # 计算金额差值和环比 - 与对比期的对比
            if len(real_money_cols) >= 1:
                current_col = real_money_cols[0]  # 当前期

                # 与对比期对比
                if len(real_money_cols) >= 2:
                    compare_col = real_money_cols[1]
                    compare_desc = date_descriptions[1]

                    # 差值列
                    diff_col = f"对比{compare_desc}金额差值"
                    result_df[diff_col] = result_df[current_col] - result_df[compare_col]

                    # 环比列 - 处理除零情况
                    ratio_col = f"对比{compare_desc}金额环比"
                    # 避免除零错误：当分母为0时，环比显示为空
                    with np.errstate(divide='ignore', invalid='ignore'):
                        ratio_values = (result_df[current_col] / result_df[compare_col] - 1)
                        ratio_values[result_df[compare_col] == 0] = np.nan  # 分母为0时设为NaN
                        result_df[ratio_col] = ratio_values.round(4)  # 保留4位小数，Excel百分比格式会显示为2位

                # 与额外对比期对比
                if len(real_money_cols) >= 3:
                    extra_compare_col = real_money_cols[2]
                    extra_compare_desc = date_descriptions[2]

                    # 差值列
                    diff_col = f"对比{extra_compare_desc}金额差值"
                    result_df[diff_col] = result_df[current_col] - result_df[extra_compare_col]

                    # 环比列 - 处理除零情况
                    ratio_col = f"对比{extra_compare_desc}金额环比"
                    # 避免除零错误：当分母为0时，环比显示为空
                    with np.errstate(divide='ignore', invalid='ignore'):
                        ratio_values = (result_df[current_col] / result_df[extra_compare_col] - 1)
                        ratio_values[result_df[extra_compare_col] == 0] = np.nan  # 分母为0时设为NaN
                        result_df[ratio_col] = ratio_values.round(4)  # 保留4位小数，Excel百分比格式会显示为2位

        logger.info(f"对比数据生成完成，共 {len(result_df)} 行 {len(result_df.columns)} 列")
        return result_df

    def get_compare_sheet(self, options: CompareOptions) -> Dict[str, Any]:
        """
        核心处理逻辑，生成需要的单个sheet

        Args:
            options: 对比选项

        Returns:
            Dict[str, Any]: sheet数据
        """
        current_data = options.current_data.copy()
        compare_data = options.compare_data.copy()
        extra_compare_data = options.extra_compare_data.copy() if options.extra_compare_data is not None else None

        # 保存引用供后续使用
        self.current_data = current_data
        self.compare_data = compare_data
        self.extra_compare_data = extra_compare_data

        # 应用过滤条件
        current_data = self.filter_data_by_options(current_data, options.filter_options or [])
        compare_data = self.filter_data_by_options(compare_data, options.filter_options or [])
        if extra_compare_data is not None:
            extra_compare_data = self.filter_data_by_options(extra_compare_data, options.filter_options or [])

        # 进行透视
        current_pivot = self.pivot_data(current_data, options.row_fields)
        compare_pivot = self.pivot_data(compare_data, options.row_fields)
        extra_compare_pivot = self.pivot_data(extra_compare_data, options.row_fields) if extra_compare_data is not None else {}

        # 获取所有数据里的rowFields合集
        row_fields_data = self.collection_fields([
            current_pivot, compare_pivot, extra_compare_pivot
        ], options.row_fields)

        # 生成对比数据
        compare_data = self.get_compare_data(row_fields_data, [
            current_pivot, compare_pivot, extra_compare_pivot
        ])

        # 获取sheet的首行标题内容
        date_range = self.get_date_range_description(current_data)
        title = f"{options.sheet_name}(发货日期{date_range})"

        return {
            'title': title,
            'data': compare_data,
            'sheet_name': options.sheet_name
        }

    def process_daily_report(self, current_excel: str, compare_excel: str,
                           extra_compare_excel: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        处理完整的日报报告

        Args:
            current_excel: 当前Excel文件路径
            compare_excel: 对比Excel文件路径
            extra_compare_excel: 额外对比Excel文件路径

        Returns:
            List[Dict[str, Any]]: 所有sheet的数据
        """
        # 读取数据
        current_data = self.read_excel_file(current_excel)
        compare_data = self.read_excel_file(compare_excel)
        extra_compare_data = None
        if extra_compare_excel:
            extra_compare_data = self.read_excel_file(extra_compare_excel)

        # 数据预处理
        current_data = self._preprocess_data(current_data)
        compare_data = self._preprocess_data(compare_data)
        if extra_compare_data is not None:
            extra_compare_data = self._preprocess_data(extra_compare_data)

        data = {
            'current_data': current_data,
            'compare_data': compare_data,
            'extra_compare_data': extra_compare_data
        }

        sheets_data = []

        # 生成各个sheet
        sheets_config = [
            {'sheet_name': '品类数据', 'row_fields': ['一级分类'], 'filter_options': []},
            {'sheet_name': '业务数据', 'row_fields': ['业务员'], 'filter_options': []},
            {'sheet_name': '业务蔬菜数据', 'row_fields': ['业务员'],
             'filter_options': [{'key': '一级分类', 'value': ['新鲜蔬菜'], 'reverse': False}]},
            {'sheet_name': '线路数据', 'row_fields': ['线路名称'], 'filter_options': []},
            {'sheet_name': '线路品类', 'row_fields': ['线路名称', '一级分类'], 'filter_options': []},
        ]

        for config in sheets_config:
            options = CompareOptions(
                current_data=current_data,
                compare_data=compare_data,
                extra_compare_data=extra_compare_data,
                row_fields=config['row_fields'],
                sheet_name=config['sheet_name'],
                filter_options=config['filter_options']
            )

            sheet_data = self.get_compare_sheet(options)
            sheets_data.append(sheet_data)
            logger.info(f"生成sheet: {sheet_data['title']}")

        logger.info(f"日报报告处理完成，共生成 {len(sheets_data)} 个sheet")
        return sheets_data