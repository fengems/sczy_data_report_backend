#!/usr/bin/env python3
"""
日报数据处理示例脚本
演示如何使用日报数据处理模块
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.processors.daily_report.entry import (
    generate_daily_report,
    generate_category_report,
    generate_sales_report,
    generate_vegetable_report,
    generate_route_report,
    generate_route_category_report,
    generate_all_reports,
)


def main():
    """主函数 - 演示日报数据处理功能"""
    print("🚀 开始日报数据处理示例")

    # 示例文件路径 - 请根据实际情况修改
    current_excel = "data/current_period.xlsx"
    compare_excel = "data/compare_period.xlsx"
    extra_compare_excel = "data/extra_compare_period.xlsx"  # 可选

    # 检查文件是否存在
    if not Path(current_excel).exists():
        print(f"❌ 当前Excel文件不存在: {current_excel}")
        print("请确保文件路径正确或修改示例脚本中的路径")
        return

    if not Path(compare_excel).exists():
        print(f"❌ 对比Excel文件不存在: {compare_excel}")
        print("请确保文件路径正确或修改示例脚本中的路径")
        return

    try:
        # 1. 生成完整的日报报告（包含所有sheet）
        print("\n📊 生成完整日报报告...")
        full_report_path = generate_daily_report(
            current_excel=current_excel,
            compare_excel=compare_excel,
            extra_compare_excel=extra_compare_excel
            if Path(extra_compare_excel).exists()
            else None,
        )
        print(f"✅ 完整日报报告已生成: {full_report_path}")

        # 2. 生成各个单独的报告
        print("\n📈 生成各个单独报告...")

        # 品类数据报告
        category_report = generate_category_report(
            current_excel=current_excel, compare_excel=compare_excel
        )
        print(f"✅ 品类数据报告已生成: {category_report}")

        # 业务数据报告
        sales_report = generate_sales_report(
            current_excel=current_excel, compare_excel=compare_excel
        )
        print(f"✅ 业务数据报告已生成: {sales_report}")

        # 业务蔬菜数据报告
        vegetable_report = generate_vegetable_report(
            current_excel=current_excel, compare_excel=compare_excel
        )
        print(f"✅ 业务蔬菜数据报告已生成: {vegetable_report}")

        # 线路数据报告
        route_report = generate_route_report(
            current_excel=current_excel, compare_excel=compare_excel
        )
        print(f"✅ 线路数据报告已生成: {route_report}")

        # 线路品类报告
        route_category_report = generate_route_category_report(
            current_excel=current_excel, compare_excel=compare_excel
        )
        print(f"✅ 线路品类报告已生成: {route_category_report}")

        # 3. 批量生成所有报告
        print("\n📦 批量生成所有报告...")
        all_reports = generate_all_reports(
            current_excel=current_excel,
            compare_excel=compare_excel,
            extra_compare_excel=extra_compare_excel
            if Path(extra_compare_excel).exists()
            else None,
            output_dir="outputs/daily_reports",
        )
        print(f"✅ 批量生成完成，共生成 {len(all_reports)} 个报告")
        for i, report_path in enumerate(all_reports, 1):
            print(f"   {i}. {report_path}")

        print("\n🎉 所有日报报告生成完成！")

    except Exception as e:
        print(f"❌ 生成报告时出错: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
