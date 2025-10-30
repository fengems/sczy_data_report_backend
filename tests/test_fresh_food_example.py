#!/usr/bin/env python3
"""
生鲜环比处理功能使用示例
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.processors.fresh_food_ratio import process_fresh_food_ratio, 函数


def example_usage():
    """使用示例"""
    print("=== 生鲜环比处理功能使用示例 ===\n")

    # 示例1: 使用英文函数名
    print("1. 使用英文函数名处理:")
    try:
        last_month_file = "downloads/订单导出_9月.xlsx"
        this_month_file = "downloads/订单导出_10月至今.xlsx"

        if Path(last_month_file).exists() and Path(this_month_file).exists():
            result_df, output_path = process_fresh_food_ratio(
                last_month_file,
                this_month_file,
                "outputs/示例输出_英文函数.xlsx"
            )

            print(f"   ✅ 处理成功!")
            print(f"   📊 结果数据形状: {result_df.shape}")
            print(f"   📁 输出文件: {output_path}")
            print(f"   🔢 前5个客户:")
            for i, row in result_df.head().iterrows():
                print(f"      {row['客户名称']}: {row['本月生鲜销售额']:.2f}元 (环比: {row['生鲜销售额环比']:.2f}%)")
        else:
            print("   ⚠️  示例文件不存在，跳过")
    except Exception as e:
        print(f"   ❌ 处理失败: {str(e)}")

    print()

    # 示例2: 使用中文函数名
    print("2. 使用中文函数名处理:")
    try:
        if Path(last_month_file).exists() and Path(this_month_file).exists():
            result_df, output_path = 函数(
                last_month_file,
                this_month_file,
                "outputs/示例输出_中文函数.xlsx"
            )

            print(f"   ✅ 处理成功!")
            print(f"   📊 结果数据形状: {result_df.shape}")
            print(f"   📁 输出文件: {output_path}")
        else:
            print("   ⚠️  示例文件不存在，跳过")
    except Exception as e:
        print(f"   ❌ 处理失败: {str(e)}")

    print()

    # 示例3: 统计信息
    print("3. 统计信息示例:")
    try:
        if Path(last_month_file).exists() and Path(this_month_file).exists():
            result_df, _ = process_fresh_food_ratio(last_month_file, this_month_file)

            total_customers = len(result_df)
            active_customers = len(result_df[result_df['本月总日活'] > 0])
            total_sales = result_df['本月生鲜销售额'].sum()
            avg_ratio = result_df['生鲜销售额环比'].mean()

            print(f"   📈 总客户数: {total_customers}")
            print(f"   👥 本月活跃客户: {active_customers}")
            print(f"   💰 本月生鲜销售总额: {total_sales:,.2f}元")
            print(f"   📊 平均生鲜销售环比: {avg_ratio:.2f}%")

            # TOP 10 客户
            top_customers = result_df.nlargest(10, '本月生鲜销售额')
            print(f"\n   🏆 销售额TOP 10客户:")
            for i, row in top_customers.iterrows():
                print(f"      {row['客户名称']}: {row['本月生鲜销售额']:,.2f}元")
        else:
            print("   ⚠️  示例文件不存在，跳过")
    except Exception as e:
        print(f"   ❌ 统计失败: {str(e)}")

    print("\n=== 使用完成 ===")


if __name__ == "__main__":
    example_usage()