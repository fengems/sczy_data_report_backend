"""
生鲜环比数据处理器
专门处理生鲜环比相关的业务逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
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
        创建基础透视表，按客户名称维度，只包含生鲜分类

        Args:
            merged_data: 合并后的数据

        Returns:
            透视表数据
        """
        # 先过滤数据，只包含生鲜分类
        fresh_data = merged_data[merged_data['一级分类'].isin(self.FRESH_CATEGORIES)]

        # 按客户名称创建透视表，只包含生鲜分类
        pivot = pd.pivot_table(
            fresh_data,
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

        logger.info(f"生鲜分类透视表创建完成，客户数: {len(pivot)}")
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
        只保留需要的列，移除多余的原始分类列

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

        # 只保留实际存在且在期望列表中的列，不添加其他列
        final_columns = [col for col in column_order if col in df.columns]

        logger.info(f"列重排序完成，最终列数: {len(final_columns)}")
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

    def get_region_pivot_data(self,
                            data: pd.DataFrame,
                            filter_options: List[Dict] = None,
                            row_fields: List[str] = None,
                            col_field: str = None,
                            value_field: str = None,
                            summary_type: str = 'sum',
                            if_save_pivot_row: bool = False) -> Union[pd.DataFrame, pd.Series]:
        """
        获取透视数据 - 实现TypeScript中的getPivotData逻辑

        Args:
            data: 已经根据日期范围过滤的数据
            filter_options: 数据筛选器选项，例: [{'key': '一级分类', 'value': ['新鲜蔬菜'], 'reverse': False}]
            row_fields: 行字段，例: ['区域名称']
            col_field: 列字段，例: '发货时间'
            value_field: 值字段，例: '客户名称' 或 '实际金额'
            summary_type: 汇总方式，'sum' 求和或 'countDist' 非重复计数
            if_save_pivot_row: 是否保存透视表行

        Returns:
            透视后的数据
        """
        if filter_options is None:
            filter_options = []
        if row_fields is None:
            row_fields = ['区域名称']

        # 1. 使用 filter_options 对数据进行筛选处理
        filtered_data = data.copy()
        for filter_option in filter_options:
            key = filter_option['key']
            values = filter_option['value']
            reverse = filter_option.get('reverse', False)

            if reverse:
                # 反向筛选：不包含这些值
                filtered_data = filtered_data[~filtered_data[key].isin(values)]
            else:
                # 正向筛选：包含这些值
                filtered_data = filtered_data[filtered_data[key].isin(values)]

        # 2. 进行透视处理
        if summary_type == 'countDist':
            # 非重复计数
            if col_field:
                # 有列字段，需要按列分组计数
                pivot_data = filtered_data.pivot_table(
                    index=row_fields,
                    columns=col_field,
                    values=value_field,
                    aggfunc=lambda x: x.nunique(),
                    fill_value=0,
                    margins=False
                )
            else:
                # 没有列字段，直接计数
                pivot_data = filtered_data.groupby(row_fields)[value_field].nunique()
        else:
            # 求和
            if col_field:
                # 有列字段，需要按列分组求和
                pivot_data = filtered_data.pivot_table(
                    index=row_fields,
                    columns=col_field,
                    values=value_field,
                    aggfunc='sum',
                    fill_value=0,
                    margins=False
                )
            else:
                # 没有列字段，直接求和
                pivot_data = filtered_data.groupby(row_fields)[value_field].sum()

        # 3. 如果有列字段，需要按日期处理
        if col_field and summary_type == 'countDist':
            # 对于countDist类型，计算平均日活：先计算每日日活，再取平均
            if isinstance(pivot_data, pd.DataFrame):
                pivot_data = pivot_data.mean(axis=1)  # 按行求平均，得到每个区域的平均日活数
        elif col_field and summary_type != 'countDist':
            # 对于数值型数据，按列求平均
            if isinstance(pivot_data, pd.DataFrame):
                pivot_data = pivot_data.mean(axis=1)

        # 4. 确保返回的数据是一维Series
        if isinstance(pivot_data, pd.DataFrame) and len(pivot_data.columns) == 1:
            pivot_data = pivot_data.iloc[:, 0]  # 转换为Series

        # 5. 根据是否保存行来返回结果
        if if_save_pivot_row:
            return pivot_data
        else:
            if isinstance(pivot_data, pd.DataFrame):
                return pivot_data.iloc[:, 0]  # 只返回值列
            else:
                return pivot_data

    def _get_week_range(self, date: datetime) -> Tuple[datetime, datetime]:
        """
        根据给定日期获取其所在周的范围（周日到周六）

        Args:
            date: 给定日期

        Returns:
            tuple: (周开始日期, 周结束日期)
        """
        # 计算这一天是周几（0=周一，6=周日）
        weekday = date.weekday()

        # 转换为周日到周六的计算
        # 如果是周日(weekday=6)，则是本周开始
        # 如果是周一(weekday=0)，则是上周的周日
        if weekday == 6:  # 周日
            week_start = date
        else:
            # 计算上周的周日
            week_start = date - timedelta(days=weekday + 1)

        # 周六 = 周日 + 6天
        week_end = week_start + timedelta(days=6)

        return week_start, week_end

    def _get_date_ranges(self, data: pd.DataFrame) -> Dict[str, Tuple[datetime, datetime]]:
        """
        获取本月、上周、上月的日期范围

        Args:
            data: 包含发货时间的数据

        Returns:
            dict: 包含各时间范围的字典
        """
        # 找到发货时间的最晚一天
        latest_date = data['发货时间'].max()

        # 本周范围：从周日到当前实际日期
        # 获取当前日期是星期几 (0=周一, 6=周日)
        weekday = latest_date.weekday()

        if weekday == 6:  # 周日
            this_week_start = latest_date  # 如果是周日，本周就是这一天
            this_week_end = latest_date
        else:
            # 计算本周的周日（找到最近的周日）
            this_week_start = latest_date - timedelta(days=weekday + 1)
            this_week_end = latest_date

        logger.info(f"本周范围计算: {latest_date.strftime('%Y-%m-%d %A')} 是周{weekday+1}, 本周范围 {this_week_start.strftime('%Y-%m-%d')} 到 {this_week_end.strftime('%Y-%m-%d')} ({(this_week_end - this_week_start).days + 1}天)")

        # 上周范围
        last_week_start = this_week_start - timedelta(weeks=1)
        last_week_end = this_week_start - timedelta(days=1)

        # 上月范围 - 假设上月是完整的一个月
        if latest_date.month == 1:
            last_month_start = datetime(latest_date.year - 1, 12, 1)
            last_month_end = datetime(latest_date.year - 1, 12, 31)
        else:
            last_month_start = datetime(latest_date.year, latest_date.month - 1, 1)
            # 计算上月最后一天
            if latest_date.month == 1:
                next_month = datetime(latest_date.year, 2, 1)
            else:
                next_month = datetime(latest_date.year, latest_date.month, 1)
            last_month_end = next_month - timedelta(days=1)

        return {
            'this_week': (this_week_start, this_week_end),
            'last_week': (last_week_start, last_week_end),
            'last_month': (last_month_start, last_month_end)
        }

    def get_table_by_date(self, date_range: Tuple[datetime, datetime], full_data: pd.DataFrame) -> pd.DataFrame:
        """
        获取日期范围内的数据 - 实现TypeScript中的getTableByDate逻辑

        Args:
            date_range: 日期范围 (start_date, end_date)
            full_data: 完整数据

        Returns:
            处理后的数据表
        """
        start_date, end_date = date_range
        # 过滤日期范围内的数据
        data = full_data[
            (full_data['发货时间'] >= start_date) &
            (full_data['发货时间'] <= end_date)
        ].copy()

        if data.empty:
            # 如果没有数据，返回空的DataFrame
            return pd.DataFrame()

        # 创建Excel表格数据
        result_data = {}

        # 1. 添加 '总活' 列
        total_active = self.get_region_pivot_data(
            data=data,
            row_fields=['区域名称'],
            value_field='客户名称',
            summary_type='countDist',
            if_save_pivot_row=True
        )
        result_data['总活'] = total_active

        # 2. 添加 '日活' 列
        daily_active = self.get_region_pivot_data(
            data=data,
            row_fields=['区域名称'],
            col_field='发货时间',
            value_field='客户名称',
            summary_type='countDist',
            if_save_pivot_row=True
        )
        result_data['日活'] = daily_active

        # 3. 添加 '蔬菜GMV' 列
        veg_gmv = self.get_region_pivot_data(
            data=data,
            filter_options=[{'key': '一级分类', 'value': ['新鲜蔬菜']}],
            row_fields=['区域名称'],
            value_field='实际金额',
            summary_type='sum',
            if_save_pivot_row=True
        )
        result_data['蔬菜GMV'] = veg_gmv

        # 4. 添加 '鲜肉GMV' 列
        meat_gmv = self.get_region_pivot_data(
            data=data,
            filter_options=[{'key': '一级分类', 'value': ['鲜肉类']}],
            row_fields=['区域名称'],
            value_field='实际金额',
            summary_type='sum',
            if_save_pivot_row=True
        )
        result_data['鲜肉GMV'] = meat_gmv

        # 5. 添加 '生鲜GMV' 列
        fresh_gmv = self.get_region_pivot_data(
            data=data,
            filter_options=[{'key': '一级分类', 'value': ['新鲜蔬菜', '鲜肉类', '豆制品']}],
            row_fields=['区域名称'],
            value_field='实际金额',
            summary_type='sum',
            if_save_pivot_row=True
        )
        result_data['生鲜GMV'] = fresh_gmv

        # 6. 添加 '标品GMV' 列
        standard_gmv = self.get_region_pivot_data(
            data=data,
            filter_options=[{'key': '一级分类', 'value': ['新鲜蔬菜', '鲜肉类', '豆制品'], 'reverse': True}],
            row_fields=['区域名称'],
            value_field='实际金额',
            summary_type='sum',
            if_save_pivot_row=True
        )
        result_data['标品GMV'] = standard_gmv

        # 7. 添加 '总GMV' 列
        total_gmv = self.get_region_pivot_data(
            data=data,
            row_fields=['区域名称'],
            value_field='实际金额',
            summary_type='sum',
            if_save_pivot_row=True
        )
        result_data['总GMV'] = total_gmv

        # 合并所有数据，确保正确的索引对齐
        try:
            result_df = pd.DataFrame(result_data)
            result_df = result_df.fillna(0)  # 填充空值为0
            logger.info(f"区域数据表生成完成，形状: {result_df.shape}")
            return result_df
        except Exception as e:
            logger.error(f"合并区域数据失败: {str(e)}")
            logger.error(f"result_data keys: {list(result_data.keys())}")
            logger.error(f"result_data types: {[type(v) for v in result_data.values()]}")
            raise

    def get_compare_data(self,
                        data1: pd.DataFrame,
                        data2: pd.DataFrame,
                        range1: Tuple[datetime, datetime],
                        range2: Tuple[datetime, datetime]) -> pd.DataFrame:
        """
        获取对比数据 - 实现TypeScript中的getCompareData逻辑

        Args:
            data1: 数据表1
            data2: 数据表2
            range1: 数据1对应的时间范围
            range2: 数据2对应的时间范围

        Returns:
            对比结果数据
        """
        # 计算日期范围内的天数
        days1 = (range1[1] - range1[0]).days + 1
        days2 = (range2[1] - range2[0]).days + 1

        # 确保两个数据表有相同的索引（区域名称）
        all_regions = set(data1.index) | set(data2.index)
        all_regions_list = sorted(list(all_regions))  # 转换为排序的list

        # 重新索引确保对齐
        data1_aligned = data1.reindex(all_regions_list, fill_value=0)
        data2_aligned = data2.reindex(all_regions_list, fill_value=0)

        # 创建对比结果
        compare_result = pd.DataFrame(index=all_regions_list)

        for col in data1.columns:
            if col in data2.columns:
                data1_values = data1_aligned[col]
                data2_values = data2_aligned[col]

                if col in ['总活', '日活']:
                    # 'subtract' 用公式 (data2 值 - data1 值)，展示的格式为数值
                    compare_result[col] = data2_values - data1_values
                else:
                    # 'monthOnMonth' 用公式 ((data2 值 / days2) - (data1 值 / days1)) / (data1 值 / days1)
                    # 展示的格式为百分比
                    avg1 = data1_values / days1
                    avg2 = data2_values / days2

                    # 避免除零错误
                    ratio = pd.Series(index=all_regions_list, dtype=float)
                    for region in all_regions_list:
                        if avg1[region] == 0:
                            ratio[region] = 0.0
                        else:
                            ratio[region] = ((avg2[region] - avg1[region]) / avg1[region]) * 100

                    compare_result[col] = ratio

        return compare_result

    def get_region_diff(self, last_month_file: str, this_month_file: str) -> pd.DataFrame:
        """
        获取区域环比数据的完整流程

        Args:
            last_month_file: 上月数据文件路径
            this_month_file: 本月数据文件路径

        Returns:
            区域环比数据
        """
        # 读取数据
        last_month_df = self.read_excel_file(last_month_file)
        this_month_df = self.read_excel_file(this_month_file)

        # 合并数据
        merged_data = self.merge_order_data(last_month_df, this_month_df)

        # 获取日期范围
        date_ranges = self._get_date_ranges(merged_data)

        # 获取各时间段的数据
        last_month_data = self.get_table_by_date(date_ranges['last_month'], merged_data)
        last_week_data = self.get_table_by_date(date_ranges['last_week'], merged_data)
        this_week_data = self.get_table_by_date(date_ranges['this_week'], merged_data)

        # 计算对比数据
        compare_res1 = self.get_compare_data(
            last_month_data, this_week_data,
            date_ranges['last_month'], date_ranges['this_week']
        )
        compare_res2 = self.get_compare_data(
            last_week_data, this_week_data,
            date_ranges['last_week'], date_ranges['this_week']
        )

        # 合并所有数据
        # 构建最终的29列数据表
        all_data = []

        # 1. 区域名称列
        all_regions = set()
        if not last_month_data.empty:
            all_regions.update(last_month_data.index)
        if not last_week_data.empty:
            all_regions.update(last_week_data.index)
        if not this_week_data.empty:
            all_regions.update(this_week_data.index)

        # 2. 组合所有数据列
        columns_order = [
            # 基数数据 (7列)
            ('上月基数', last_month_data),
            ('上周基数', last_week_data),
            ('本周数据', this_week_data),
            # 对比数据 (2个7列 = 14列)
            ('环比上月', compare_res1),
            ('环比上周', compare_res2)
        ]

        # 构建最终结果
        result_data = {}
        for section_name, data in columns_order:
            if not data.empty:
                for col in data.columns:
                    result_data[f"{section_name}_{col}"] = data[col]

        # 添加区域名称作为索引，确保index是list而不是set
        result_df = pd.DataFrame(result_data, index=sorted(list(all_regions)))
        result_df = result_df.fillna(0)

        # 重置索引，将区域名称作为列
        result_df = result_df.reset_index()
        result_df = result_df.rename(columns={'index': '区域名称'})

        # 保存最新日期信息到结果中
        result_df.latest_date = merged_data['发货时间'].max().strftime('%m月%d日')

        logger.info(f"区域环比数据计算完成，共 {len(result_df)} 个区域")
        return result_df

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