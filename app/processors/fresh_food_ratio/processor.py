"""
生鲜环比数据处理器
专门处理生鲜环比相关的业务逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

from app.processors.utils.base_excel_processor import BaseExcelProcessor

logger = logging.getLogger(__name__)


class FreshFoodRatioProcessor(BaseExcelProcessor):
    """生鲜环比数据处理器"""

    # 生鲜分类定义
    FRESH_CATEGORIES = ['新鲜蔬菜', '鲜肉类', '豆制品']

    def __init__(self):
        """初始化处理器"""
        required_columns = [
            '客户名称', '业务员', '发货时间', '实际金额', '一级分类'
        ]
        super().__init__(required_columns)

    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """
        读取生鲜环比Excel文件，并进行数据清理

        Args:
            file_path: Excel文件路径

        Returns:
            清理后的DataFrame
        """
        df = super().read_excel_file(file_path)

        # 清理数据
        df = self.clean_datetime_column(df, '发货时间')
        df = self.clean_numeric_column(df, '实际金额')

        return df

    def merge_order_data(self, last_month_df: pd.DataFrame, this_month_df: pd.DataFrame) -> pd.DataFrame:
        """
        合并上月和本月的订单数据

        Args:
            last_month_df: 上月订单数据
            this_month_df: 本月订单数据

        Returns:
            合并后的数据
        """
        # 为数据添加月份标识
        last_month_df = last_month_df.copy()
        this_month_df = this_month_df.copy()

        last_month_df['月份'] = '上月'
        this_month_df['月份'] = '本月'

        # 合并数据
        all_data = pd.concat([last_month_df, this_month_df], ignore_index=True)

        # 1. 筛选：客户名称不为空
        all_data = all_data.dropna(subset=['客户名称'])
        all_data = all_data[all_data['客户名称'].str.strip() != '']

        # 2. 排序：按发货时间降序（最新日期在前面）
        all_data = all_data.sort_values('发货时间', ascending=False)

        logger.info(f"合并后数据总行数: {len(all_data)}")
        logger.info(f"上月数据: {len(last_month_df)} 行")
        logger.info(f"本月数据: {len(this_month_df)} 行")

        return all_data

    def calculate_order_days(self, merged_data: pd.DataFrame) -> Tuple[int, int]:
        """
        计算下单天数

        Args:
            merged_data: 合并后的数据

        Returns:
            tuple: (上月天数, 本月天数)
        """
        last_month_data = merged_data[merged_data['月份'] == '上月']
        this_month_data = merged_data[merged_data['月份'] == '本月']

        last_days = len(last_month_data['发货时间'].dt.date.unique())
        this_days = len(this_month_data['发货时间'].dt.date.unique())

        logger.info(f"上月下单天数: {last_days}")
        logger.info(f"本月下单天数: {this_days}")

        return last_days, this_days

    def create_pivot_table_base(self, merged_data: pd.DataFrame) -> pd.DataFrame:
        """
        创建基础透视表，按客户名称维度

        Args:
            merged_data: 合并后的数据

        Returns:
            透视表数据
        """
        # 按客户名称创建透视表
        pivot = pd.pivot_table(
            merged_data,
            values='实际金额',
            index='客户名称',
            columns='一级分类',
            aggfunc='sum',
            fill_value=0,
            margins=False
        ).reset_index()

        # 确保所有生鲜分类都存在
        for category in self.FRESH_CATEGORIES:
            if category not in pivot.columns:
                pivot[category] = 0

        logger.info(f"透视表创建完成，客户数: {len(pivot)}")
        return pivot

    def get_latest_salesman(self, merged_data: pd.DataFrame, customer_name: str) -> str:
        """
        获取客户的最新业务员（类似Excel XLOOKUP功能）

        Args:
            merged_data: 合并后的数据（已按发货时间降序排序）
            customer_name: 客户名称

        Returns:
            最新业务员名称
        """
        customer_data = merged_data[merged_data['客户名称'] == customer_name]
        if not customer_data.empty:
            # 取第一条记录的业务员（因为数据已按发货时间降序排序）
            return customer_data.iloc[0]['业务员']
        return ''

    def calculate_sales_data(self, merged_data: pd.DataFrame, category: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        计算指定分类的销售数据

        Args:
            merged_data: 合并后的数据
            category: 商品分类

        Returns:
            tuple: (上月销售数据, 本月销售数据)
        """
        # 按客户和月份分类汇总
        category_data = merged_data[merged_data['一级分类'] == category]

        # 按客户和月份分组汇总
        sales_summary = category_data.groupby(['客户名称', '月份'])['实际金额'].sum().unstack(fill_value=0)

        # 确保两列都存在
        if '上月' not in sales_summary.columns:
            sales_summary['上月'] = 0
        if '本月' not in sales_summary.columns:
            sales_summary['本月'] = 0

        # 重命名列
        last_month_col = f'上月{category}销售额'
        this_month_col = f'本月{category}销售额'

        last_month_data = sales_summary[['上月']].rename(columns={'上月': last_month_col})
        this_month_data = sales_summary[['本月']].rename(columns={'本月': this_month_col})

        logger.info(f"{category}销售数据计算完成")
        return last_month_data, this_month_data

    def calculate_daily_active(self, merged_data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        计算日活数据

        Args:
            merged_data: 合并后的数据

        Returns:
            tuple: (上月日活数据, 本月日活数据)
        """
        # 按客户和月份计算去重后的日活
        daily_active = merged_data.groupby(['客户名称', '月份'])['发货时间'].nunique().unstack(fill_value=0)

        # 确保两列都存在
        if '上月' not in daily_active.columns:
            daily_active['上月'] = 0
        if '本月' not in daily_active.columns:
            daily_active['本月'] = 0

        # 重命名列
        last_month_active = daily_active[['上月']].rename(columns={'上月': '上月总日活'})
        this_month_active = daily_active[['本月']].rename(columns={'本月': '本月总日活'})

        logger.info(f"日活数据计算完成")
        return last_month_active, this_month_active

    def calculate_ratio(self, this_month_value: float, last_month_value: float) -> float:
        """
        计算环比

        Args:
            this_month_value: 本月数值
            last_month_value: 上月数值

        Returns:
            环比百分比
        """
        if last_month_value == 0:
            return 0.0
        return round((this_month_value - last_month_value) / last_month_value * 100, 2)

    def _reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重新排列列的顺序，让环比列紧跟在对应数据列后面

        Args:
            df: 原始DataFrame

        Returns:
            重新排列后的DataFrame
        """
        # 定义列的顺序
        column_order = [
            '客户名称', '业务员',
            '本月总日活', '上月总日活', '总日活环比',
            '本月新鲜蔬菜销售额', '上月新鲜蔬菜销售额', '蔬菜销售额环比',
            '本月鲜肉类销售额', '上月鲜肉类销售额', '鲜肉销售额环比',
            '本月豆制品销售额', '上月豆制品销售额', '豆制品销售额环比',
            '本月生鲜销售额', '上月生鲜销售额', '生鲜销售额环比'
        ]

        # 筛选实际存在的列
        existing_columns = [col for col in column_order if col in df.columns]

        # 添加其他未在order中的列
        other_columns = [col for col in df.columns if col not in existing_columns]

        final_columns = existing_columns + other_columns
        return df[final_columns]

    def get_customer_diff(self, last_month_file: str, this_month_file: str) -> pd.DataFrame:
        """
        获取客户环比数据的完整流程

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径

        Returns:
            客户环比数据
        """
        # 读取数据
        last_month_df = self.read_excel_file(last_month_file)
        this_month_df = self.read_excel_file(this_month_file)

        # 合并数据
        merged_data = self.merge_order_data(last_month_df, this_month_df)

        # 记录最新日期用于Excel表头
        latest_date = merged_data['发货时间'].max().strftime('%m月%d日')

        # 计算日活数据
        last_active, this_active = self.calculate_daily_active(merged_data)

        # 创建基础透视表
        pivot_base = self.create_pivot_table_base(merged_data)

        # 计算各分类销售数据
        sales_data = {}
        for category in self.FRESH_CATEGORIES:
            last_sales, this_sales = self.calculate_sales_data(merged_data, category)
            sales_data[category] = {
                'last': last_sales,
                'this': this_sales
            }

        # 合并所有数据
        result = pivot_base.copy()

        # 添加日活数据
        result = result.merge(this_active, left_on='客户名称', right_index=True, how='left')
        result = result.merge(last_active, left_on='客户名称', right_index=True, how='left')

        # 添加各分类销售数据
        for category in self.FRESH_CATEGORIES:
            result = result.merge(sales_data[category]['this'], left_on='客户名称', right_index=True, how='left')
            result = result.merge(sales_data[category]['last'], left_on='客户名称', right_index=True, how='left')

        # 计算生鲜总销售额
        result['本月生鲜销售额'] = result['本月新鲜蔬菜销售额'] + result['本月鲜肉类销售额'] + result['本月豆制品销售额']
        result['上月生鲜销售额'] = result['上月新鲜蔬菜销售额'] + result['上月鲜肉类销售额'] + result['上月豆制品销售额']

        # 添加最新业务员信息
        result['业务员'] = result['客户名称'].apply(lambda x: self.get_latest_salesman(merged_data, x))

        # 计算环比
        result['总日活环比'] = result.apply(
            lambda row: self.calculate_ratio(row['本月总日活'], row['上月总日活']), axis=1
        )
        result['蔬菜销售额环比'] = result.apply(
            lambda row: self.calculate_ratio(row['本月新鲜蔬菜销售额'], row['上月新鲜蔬菜销售额']), axis=1
        )
        result['鲜肉销售额环比'] = result.apply(
            lambda row: self.calculate_ratio(row['本月鲜肉类销售额'], row['上月鲜肉类销售额']), axis=1
        )
        result['豆制品销售额环比'] = result.apply(
            lambda row: self.calculate_ratio(row['本月豆制品销售额'], row['上月豆制品销售额']), axis=1
        )
        result['生鲜销售额环比'] = result.apply(
            lambda row: self.calculate_ratio(row['本月生鲜销售额'], row['上月生鲜销售额']), axis=1
        )

        # 填充NaN值
        result = result.fillna(0)

        # 重新排列列的顺序
        result = self._reorder_columns(result)

        # 保存最新日期信息到结果中
        result.latest_date = latest_date

        logger.info(f"客户环比数据计算完成，共 {len(result)} 个客户")
        return result

    def process(self, last_month_file: str, this_month_file: str) -> pd.DataFrame:
        """
        实现基类的抽象方法

        Args:
            last_month_file: 上月数据文件
            this_month_file: 本月数据文件

        Returns:
            处理后的数据
        """
        return self.get_customer_diff(last_month_file, this_month_file)