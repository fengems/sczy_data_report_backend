"""
Excel数据处理核心模块
实现生鲜环比数据处理功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FreshFoodRatioProcessor:
    """生鲜环比数据处理器"""

    def __init__(self):
        """初始化处理器"""
        self.required_columns = [
            '客户名称', '业务员', '发货时间', '实际金额', '一级分类'
        ]

    def validate_columns(self, df: pd.DataFrame, file_name: str) -> bool:
        """验证DataFrame是否包含必要的列"""
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"文件 {file_name} 缺少必要的列: {missing_columns}")
            return False
        return True

    def read_excel_file(self, file_path: str) -> pd.DataFrame:
        """读取Excel文件"""
        try:
            logger.info(f"正在读取文件: {file_path}")
            df = pd.read_excel(file_path, sheet_name=0)  # 读取第一个sheet

            # 标准化列名（去除空格）
            df.columns = df.columns.str.strip()

            if not self.validate_columns(df, file_path):
                raise ValueError(f"文件 {file_path} 缺少必要的列")

            # 转换发货时间为datetime类型
            df['发货时间'] = pd.to_datetime(df['发货时间'])

            # 转换实际金额为数值类型，处理可能的字符串
            if '实际金额' in df.columns:
                df['实际金额'] = pd.to_numeric(df['实际金额'], errors='coerce').fillna(0)

            logger.info(f"成功读取文件 {file_path}，共 {len(df)} 行数据")
            return df

        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            raise

    def merge_order_data(self, last_month_df: pd.DataFrame, this_month_df: pd.DataFrame) -> pd.DataFrame:
        """合并上个月和本月的订单数据"""
        logger.info("正在合并订单数据...")

        # 添加月份标识
        last_month_df['月份'] = '上月'
        this_month_df['月份'] = '本月'

        # 合并数据
        all_area = pd.concat([last_month_df, this_month_df], ignore_index=True)

        # 1. 筛选：客户名称不为空
        all_area = all_area.dropna(subset=['客户名称'])
        all_area = all_area[all_area['客户名称'].str.strip() != '']

        # 2. 排序：按发货时间降序（最新日期在前面）
        all_area = all_area.sort_values('发货时间', ascending=False)

        logger.info(f"数据合并完成，共 {len(all_area)} 行数据")
        logger.info(f"筛选排序后，客户数量: {len(all_area['客户名称'].unique())}")
        return all_area

    def get_latest_salesman(self, all_area: pd.DataFrame, customers: pd.Series) -> pd.DataFrame:
        """
        使用类似XLOOKUP逻辑获取每个客户的最新业务员

        Args:
            all_area: 排序后的完整订单数据
            customers: 客户名称列表

        Returns:
            包含客户名称和最新业务员的DataFrame
        """
        logger.info("正在获取客户最新业务员...")

        latest_salesmen = []

        for customer in customers:
            # 找到该客户的所有记录
            customer_records = all_area[all_area['客户名称'] == customer]

            if not customer_records.empty:
                # 获取最新的业务员（第一条记录，因为数据已按发货时间降序排序）
                latest_salesman = customer_records.iloc[0]['业务员']
                latest_salesmen.append({
                    '客户名称': customer,
                    '业务员': latest_salesman
                })

        salesman_df = pd.DataFrame(latest_salesmen)
        logger.info(f"获取到 {len(salesman_df)} 个客户的最新业务员信息")
        return salesman_df

    def calculate_order_days(self, all_area: pd.DataFrame) -> Tuple[int, int]:
        """计算上个月和本月的下单天数"""
        # 按月份分组，计算每天有订单的天数
        daily_orders = all_area.groupby(['月份', all_area['发货时间'].dt.date]).size().reset_index()

        last_month_days = len(daily_orders[daily_orders['月份'] == '上月'])
        this_month_days = len(daily_orders[daily_orders['月份'] == '本月'])

        logger.info(f"上月下单天数: {last_month_days}, 本月下单天数: {this_month_days}")
        return last_month_days, this_month_days

    def create_pivot_table_base(self, all_area: pd.DataFrame) -> pd.DataFrame:
        """创建基础透视表"""
        logger.info("正在创建基础透视表...")

        # 基础透视表：只使用客户名称作为行
        unique_customers = all_area['客户名称'].unique()
        pivot_table = pd.DataFrame({'客户名称': unique_customers})

        # 使用XLOOKUP逻辑获取最新业务员
        latest_salesmen_df = self.get_latest_salesman(all_area, pivot_table['客户名称'])
        pivot_table = pivot_table.merge(latest_salesmen_df, on='客户名称', how='left')

        logger.info(f"基础透视表创建完成，共 {len(pivot_table)} 个唯一客户")
        return pivot_table

    def calculate_daily_active_data(self, all_area: pd.DataFrame, last_month_days: int, this_month_days: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """计算日活数据"""
        logger.info("正在计算日活数据...")

        # 计算每个客户的日活数据（按发货时间去重计数）
        daily_active = all_area.pivot_table(
            index='客户名称',
            values='发货时间',
            aggfunc=lambda x: x.dt.date.nunique(),  # 按日期去重计数
            fill_value=0
        ).reset_index()

        # 按月份分别计算
        last_month_daily = all_area[all_area['月份'] == '上月'].pivot_table(
            index='客户名称',
            values='发货时间',
            aggfunc=lambda x: x.dt.date.nunique(),
            fill_value=0
        ).reset_index().rename(columns={'发货时间': '上月总日活'})

        this_month_daily = all_area[all_area['月份'] == '本月'].pivot_table(
            index='客户名称',
            values='发货时间',
            aggfunc=lambda x: x.dt.date.nunique(),
            fill_value=0
        ).reset_index().rename(columns={'发货时间': '本月总日活'})

        return last_month_daily, this_month_daily

    def calculate_sales_data(self, all_area: pd.DataFrame, category: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """计算特定分类的销售数据"""
        logger.info(f"正在计算 {category} 销售数据...")

        # 筛选指定分类的数据
        category_data = all_area[all_area['一级分类'] == category]

        # 按月份分别计算销售额
        last_month_sales = category_data[category_data['月份'] == '上月'].pivot_table(
            index='客户名称',
            values='实际金额',
            aggfunc='sum',
            fill_value=0
        ).reset_index().rename(columns={'实际金额': f'上月{category}销售额'})

        this_month_sales = category_data[category_data['月份'] == '本月'].pivot_table(
            index='客户名称',
            values='实际金额',
            aggfunc='sum',
            fill_value=0
        ).reset_index().rename(columns={'实际金额': f'本月{category}销售额'})

        return last_month_sales, this_month_sales

    def calculate_ratio(self, current_value: float, last_value: float) -> float:
        """计算环比值"""
        if last_value == 0:
            return 0.0
        return ((current_value - last_value) / last_value) * 100

    def merge_data_to_pivot(self, pivot_table: pd.DataFrame, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """将各种数据合并到透视表"""
        result = pivot_table.copy()

        for key, df in data_dict.items():
            if df is not None and not df.empty:
                result = result.merge(df, on='客户名称', how='left')

        return result

    def _reorder_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重新排列列的顺序，将环比列放在对应数据列后面

        Args:
            df: 原始DataFrame

        Returns:
            重新排列后的DataFrame
        """
        # 定义列的新顺序
        column_order = [
            '客户名称', '业务员',
            '上月总日活', '本月总日活', '总日活环比',
            '上月新鲜蔬菜销售额', '本月新鲜蔬菜销售额', '蔬菜销售额环比',
            '上月鲜肉类销售额', '本月鲜肉类销售额', '鲜肉销售额环比',
            '上月豆制品销售额', '本月豆制品销售额', '豆制品销售额环比',
            '上月生鲜销售额', '本月生鲜销售额', '生鲜销售额环比'
        ]

        # 过滤出实际存在的列
        existing_columns = [col for col in column_order if col in df.columns]

        # 添加其他可能存在的列（不在预定义顺序中的）
        other_columns = [col for col in df.columns if col not in existing_columns]

        final_columns = existing_columns + other_columns

        return df[final_columns]

    def get_customer_diff(self, last_month_order_file: str, this_month_order_file: str) -> pd.DataFrame:
        """
        获取客户环比的sheet数据

        Args:
            last_month_order_file: 上个月订单数据的Excel文件地址
            this_month_order_file: 本月订单数据的Excel文件地址

        Returns:
            包含客户环比数据的DataFrame
        """
        logger.info("开始处理客户环比数据...")

        try:
            # 1. 读取Excel文件
            last_month_df = self.read_excel_file(last_month_order_file)
            this_month_df = self.read_excel_file(this_month_order_file)

            # 2. 合并数据
            all_area = self.merge_order_data(last_month_df, this_month_df)

            # 3. 创建基础透视表
            pivot_table = self.create_pivot_table_base(all_area)

            # 4. 计算下单天数
            last_month_days, this_month_days = self.calculate_order_days(all_area)

            # 5. 计算日活数据
            last_month_daily, this_month_daily = self.calculate_daily_active_data(all_area, last_month_days, this_month_days)

            # 6. 计算蔬菜销售数据
            veg_last, veg_this = self.calculate_sales_data(all_area, '新鲜蔬菜')

            # 7. 计算鲜肉销售数据
            meat_last, meat_this = self.calculate_sales_data(all_area, '鲜肉类')

            # 8. 计算豆制品销售数据
            bean_last, bean_this = self.calculate_sales_data(all_area, '豆制品')

            # 9. 计算生鲜总销售数据（三个分类合并）
            fresh_categories = ['新鲜蔬菜', '鲜肉类', '豆制品']
            fresh_data = all_area[all_area['一级分类'].isin(fresh_categories)]

            fresh_last = fresh_data[fresh_data['月份'] == '上月'].pivot_table(
                index='客户名称',
                values='实际金额',
                aggfunc='sum',
                fill_value=0
            ).reset_index().rename(columns={'实际金额': '上月生鲜销售额'})

            fresh_this = fresh_data[fresh_data['月份'] == '本月'].pivot_table(
                index='客户名称',
                values='实际金额',
                aggfunc='sum',
                fill_value=0
            ).reset_index().rename(columns={'实际金额': '本月生鲜销售额'})

            # 10. 合并所有数据到透视表
            data_dict = {
                'last_month_daily': last_month_daily,
                'this_month_daily': this_month_daily,
                'veg_last': veg_last,
                'veg_this': veg_this,
                'meat_last': meat_last,
                'meat_this': meat_this,
                'bean_last': bean_last,
                'bean_this': bean_this,
                'fresh_last': fresh_last,
                'fresh_this': fresh_this
            }

            result = self.merge_data_to_pivot(pivot_table, data_dict)

            # 确保所有数值列都是数值类型
            numeric_columns = [
                '本月总日活', '上月总日活',
                '本月新鲜蔬菜销售额', '上月新鲜蔬菜销售额',
                '本月鲜肉类销售额', '上月鲜肉类销售额',
                '本月豆制品销售额', '上月豆制品销售额',
                '本月生鲜销售额', '上月生鲜销售额'
            ]

            for col in numeric_columns:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)

            # 11. 计算各种环比数据
            # 日活环比
            result['总日活环比'] = result.apply(
                lambda row: self.calculate_ratio(
                    row.get('本月总日活', 0) / this_month_days if this_month_days > 0 else 0,
                    row.get('上月总日活', 0) / last_month_days if last_month_days > 0 else 0
                ),
                axis=1
            )

            # 蔬菜销售额环比
            result['蔬菜销售额环比'] = result.apply(
                lambda row: self.calculate_ratio(
                    row.get('本月新鲜蔬菜销售额', 0) / this_month_days if this_month_days > 0 else 0,
                    row.get('上月新鲜蔬菜销售额', 0) / last_month_days if last_month_days > 0 else 0
                ),
                axis=1
            )

            # 鲜肉销售额环比
            result['鲜肉销售额环比'] = result.apply(
                lambda row: self.calculate_ratio(
                    row.get('本月鲜肉类销售额', 0) / this_month_days if this_month_days > 0 else 0,
                    row.get('上月鲜肉类销售额', 0) / last_month_days if last_month_days > 0 else 0
                ),
                axis=1
            )

            # 豆制品销售额环比
            result['豆制品销售额环比'] = result.apply(
                lambda row: self.calculate_ratio(
                    row.get('本月豆制品销售额', 0) / this_month_days if this_month_days > 0 else 0,
                    row.get('上月豆制品销售额', 0) / last_month_days if last_month_days > 0 else 0
                ),
                axis=1
            )

            # 生鲜总销售额环比
            result['生鲜销售额环比'] = result.apply(
                lambda row: self.calculate_ratio(
                    row.get('本月生鲜销售额', 0) / this_month_days if this_month_days > 0 else 0,
                    row.get('上月生鲜销售额', 0) / last_month_days if last_month_days > 0 else 0
                ),
                axis=1
            )

            # 12. 填充空值为0
            result = result.fillna(0)

            # 13. 重新排列列的顺序，将环比列放在对应数据列后面
            result = self._reorder_columns(result)

            # 14. 按生鲜销售额降序排列
            result = result.sort_values('本月生鲜销售额', ascending=False)

            # 15. 添加最新日期信息用于Excel表头
            if not all_area.empty:
                latest_date = all_area['发货时间'].max().day
                result.latest_date = latest_date
                logger.info(f"数据最新日期: {latest_date}日")

            logger.info(f"客户环比数据处理完成，共 {len(result)} 个客户")
            return result

        except Exception as e:
            logger.error(f"处理客户环比数据失败: {str(e)}")
            raise


def get_customer_diff(last_month_order_file: str, this_month_order_file: str) -> pd.DataFrame:
    """
    获取客户环比数据的便捷函数

    Args:
        last_month_order_file: 上个月订单数据的Excel文件地址
        this_month_order_file: 本月订单数据的Excel文件地址

    Returns:
        包含客户环比数据的DataFrame
    """
    processor = FreshFoodRatioProcessor()
    return processor.get_customer_diff(last_month_order_file, this_month_order_file)