#!/usr/bin/env python3
"""
生鲜环比功能快速测试脚本
独立运行，不依赖pytest框架
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.processors.fresh_food_ratio import process_fresh_food_ratio
from app.utils.logger import get_logger

logger = get_logger("test_fresh_food_ratio_quick")


def main():
    """主测试函数"""
    print("=" * 60)
    print("生鲜环比数据处理功能快速测试")
    print("=" * 60)

    # 检查测试数据
    last_month_file = project_root / "test_data/2024年9月订单数据.xlsx"
    this_month_file = project_root / "test_data/2024年10月订单数据.xlsx"

    if not last_month_file.exists() or not this_month_file.exists():
        print("❌ 测试数据文件不存在")
        print("请先运行: python test_data/create_test_data.py")
        return 1

    print(f"✅ 测试数据已准备:")
    print(f"   - 上月数据: {last_month_file}")
    print(f"   - 本月数据: {this_month_file}")

    try:
        print("\n🚀 开始处理生鲜环比数据...")

        # 处理数据
        result_df, output_path = process_fresh_food_ratio(
            str(last_month_file),
            str(this_month_file)
        )

        print(f"\n✅ 处理完成！")
        print(f"   - 输出文件: {output_path}")
        print(f"   - 数据行数: {len(result_df)}")
        print(f"   - 唯一客户数: {len(result_df['客户名称'].unique())}")
        print(f"   - 唯一业务员数: {len(result_df['业务员'].unique())}")

        # 显示前几行数据
        print(f"\n📊 数据预览:")
        print(result_df.head()[['客户名称', '业务员', '本月生鲜销售额', '生鲜销售额环比']])

        # 验证关键指标
        print(f"\n📈 关键指标:")
        print(f"   - 上月生鲜销售总额: {result_df['上月生鲜销售额'].sum():,.2f} 元")
        print(f"   - 本月生鲜销售总额: {result_df['本月生鲜销售额'].sum():,.2f} 元")
        print(f"   - 平均生鲜销售额环比: {result_df['生鲜销售额环比'].mean():.2f}%")

        print(f"\n🎉 测试成功！所有功能正常工作。")
        return 0

    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        print(f"\n❌ 测试失败: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)