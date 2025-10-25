"""
生鲜环比Excel写入器
专门处理生鲜环比报告的Excel输出和格式化
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, Optional, Union

from app.outputs.utils.base_excel_writer import BaseExcelWriter

logger = logging.getLogger(__name__)


class FreshFoodRatioExcelWriter(BaseExcelWriter):
    """生鲜环比Excel写入器"""

    def __init__(self):
        """初始化写入器"""
        super().__init__()

    def apply_excel_formatting(self, writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame):
        """
        为生鲜环比Excel工作表应用专门的格式化

        Args:
            writer: Excel写入器
            sheet_name: 工作表名称
            df: 数据DataFrame
        """
        try:
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # 定义格式
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'vcenter',  # 垂直居中
                'align': 'center',    # 水平居中
                'fg_color': '#D7E4BD',  # 浅绿色背景
                'border': 1
            })

            number_format = workbook.add_format({'num_format': '#,##0.00'})
            percentage_format = workbook.add_format({'num_format': '0.00%'})
            currency_format = workbook.add_format({'num_format': '¥#,##0.00'})

            # 负值条件格式：浅红填充深红色文本
            negative_format = workbook.add_format({
                'font_color': '#9C0006',  # 深红色文本
                'bg_color': '#FFC7CE',   # 浅红色填充
                'num_format': '#,##0.00'
            })

            negative_percentage_format = workbook.add_format({
                'font_color': '#9C0006',  # 深红色文本
                'bg_color': '#FFC7CE',   # 浅红色填充
                'num_format': '0.00%'
            })

            # 设置列宽：第一列25字符，其他列12字符
            for col_num, column in enumerate(df.columns):
                if col_num == 0:  # 第一列
                    width = 25
                else:  # 其他列
                    width = 12
                worksheet.set_column(col_num, col_num, width)

            # 格式化标题行（现在在第1行，因为第0行是合并表头）
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(1, col_num, value, header_format)

            # 格式化数据行（从第2行开始）
            for row_num in range(2, len(df) + 2):
                for col_num, column in enumerate(df.columns):
                    value = df.iloc[row_num - 2, col_num]

                    # 跳过客户名称和业务员列
                    if column in ['客户名称', '业务员']:
                        worksheet.write(row_num, col_num, value)
                    # 环比列使用百分比格式，负值使用特殊格式
                    elif '环比' in column:
                        if pd.notna(value) and isinstance(value, (int, float)) and value < 0:
                            worksheet.write(row_num, col_num, value / 100, negative_percentage_format)
                        else:
                            worksheet.write(row_num, col_num, value / 100 if pd.notna(value) and isinstance(value, (int, float)) else 0, percentage_format)
                    # 销售额列使用货币格式，负值使用特殊格式
                    elif '销售额' in column:
                        if pd.notna(value) and isinstance(value, (int, float)) and value < 0:
                            worksheet.write(row_num, col_num, value, negative_format)
                        else:
                            worksheet.write(row_num, col_num, value, currency_format)
                    # 其他数值列使用数字格式，负值使用特殊格式
                    elif isinstance(value, (int, float)):
                        if pd.notna(value) and value < 0:
                            worksheet.write(row_num, col_num, value, negative_format)
                        else:
                            worksheet.write(row_num, col_num, value, number_format)
                    else:
                        worksheet.write(row_num, col_num, value)

            # 冻结标题行（冻结第2行及以下）
            worksheet.freeze_panes(2, 0)

            # 添加筛选器（从第1行开始，到最后一行）
            worksheet.autofilter(1, 0, len(df) + 1, len(df.columns) - 1)

            logger.info(f"工作表 {sheet_name} 格式化完成")

        except Exception as e:
            logger.warning(f"应用Excel格式化失败: {str(e)}")
            # 如果格式化失败，至少确保数据写入成功
            pass

    def _add_merged_header(self, writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame):
        """
        添加合并的表头

        Args:
            writer: Excel写入器
            sheet_name: 工作表名称
            df: 数据DataFrame
        """
        try:
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # 获取数据中的最新日期
            latest_date = None
            if hasattr(df, 'latest_date') and getattr(df, 'latest_date', None):
                latest_date = getattr(df, 'latest_date')
            else:
                # 如果没有最新日期信息，使用当前日期
                latest_date = datetime.now().day

            # 创建表头文案
            header_text = f'客户生鲜环比截止 {latest_date}'

            # 定义表头格式
            header_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#4F81BD',  # 蓝色背景
                'font_color': 'white',
                'border': 1
            })

            # 合并单元格：从第一行开始，跨越所有列
            total_columns = len(df.columns)
            worksheet.merge_range(
                0, 0, 0, total_columns - 1,  # 第一行，从第0列到最后一列
                header_text,
                header_format
            )

            # 设置行高
            worksheet.set_row(0, 30)  # 设置第一行高度

            logger.info(f"已添加合并表头: {header_text}")

        except Exception as e:
            logger.warning(f"添加合并表头失败: {str(e)}")

    def _add_summary_sheet(self, writer: pd.ExcelWriter, customer_diff_df: pd.DataFrame):
        """
        添加数据摘要工作表

        Args:
            writer: Excel写入器
            customer_diff_df: 客户环比数据
        """
        try:
            logger.info("正在生成数据摘要...")

            # 计算摘要数据
            summary_data = {
                '指标': [
                    '总客户数',
                    '本月活跃客户数',
                    '上月活跃客户数',
                    '本月生鲜销售总额',
                    '上月生鲜销售总额',
                    '生鲜销售额总环比',
                    '平均日活环比',
                    '生鲜销售TOP10客户数'
                ],
                '数值': [
                    len(customer_diff_df),
                    len(customer_diff_df[customer_diff_df['本月总日活'] > 0]),
                    len(customer_diff_df[customer_diff_df['上月总日活'] > 0]),
                    customer_diff_df['本月生鲜销售额'].sum(),
                    customer_diff_df['上月生鲜销售额'].sum(),
                    customer_diff_df['生鲜销售额环比'].mean(),
                    customer_diff_df['总日活环比'].mean(),
                    10  # TOP10客户数
                ],
                '单位': [
                    '个', '个', '个', '元', '元', '%', '%', '个'
                ]
            }

            summary_df = pd.DataFrame(summary_data)

            # 写入摘要数据
            summary_df.to_excel(
                writer,
                sheet_name='数据摘要',
                index=False
            )

            # 应用基础格式化
            column_widths = {
                '指标': 20,
                '数值': 15,
                '单位': 10
            }
            self.apply_basic_formatting(writer, '数据摘要', summary_df, column_widths=column_widths)

            logger.info("数据摘要生成完成")

        except Exception as e:
            logger.warning(f"生成数据摘要失败: {str(e)}")

    def write_report(self, customer_diff_df: pd.DataFrame,
                    output_file: Optional[Union[str, Path]] = None) -> str:
        """
        写入生鲜环比报告

        Args:
            customer_diff_df: 客户环比数据
            output_file: 输出文件路径，如果为None则自动生成

        Returns:
            生成的文件路径
        """
        try:
            # 生成输出文件名
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.default_output_dir / f"生鲜环比报告_{timestamp}.xlsx"
            else:
                output_file = Path(output_file)

            logger.info(f"正在生成生鲜环比报告: {output_file}")

            # 创建Excel写入器
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                # 写入客户环比数据
                logger.info("正在写入客户环比数据...")
                customer_diff_df.to_excel(
                    writer,
                    sheet_name='客户环比',
                    index=False,
                    startrow=1  # 从第二行开始，为表头留空间
                )

                # 应用专门的格式化
                self.apply_excel_formatting(writer, '客户环比', customer_diff_df)

                # 添加合并的表头
                self._add_merged_header(writer, '客户环比', customer_diff_df)

                # 添加数据摘要工作表
                self._add_summary_sheet(writer, customer_diff_df)

            logger.info(f"生鲜环比报告生成成功: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"生成生鲜环比报告失败: {str(e)}")
            raise