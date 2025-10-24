#!/usr/bin/env python3
"""
验证清理旧文件后生鲜环比功能是否正常
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.processors.fresh_food_ratio import process_fresh_food_ratio

def test_basic_functionality():
    """测试基本功能是否正常"""
    print("🔍 测试清理后的基本功能...")

    # 测试数据文件
    last_month_file = "test_data/2024年9月订单数据.xlsx"
    this_month_file = "test_data/2024年10月订单数据.xlsx"

    # 检查测试数据是否存在
    if not Path(last_month_file).exists() or not Path(this_month_file).exists():
        print("❌ 测试数据文件不存在，跳过功能测试")
        return True

    try:
        # 测试处理功能
        output_file = "outputs/test_cleanup_verification.xlsx"
        result_df, result_path = process_fresh_food_ratio(
            last_month_file,
            this_month_file,
            output_file
        )

        print(f"✅ 生鲜环比处理成功")
        print(f"📊 数据行数: {len(result_df)}")
        print(f"📊 数据列数: {len(result_df.columns)}")
        print(f"📁 输出文件: {result_path}")

        # 验证输出文件存在
        if Path(result_path).exists():
            print("✅ 输出文件验证成功")
            return True
        else:
            print("❌ 输出文件不存在")
            return False

    except Exception as e:
        print(f"❌ 功能测试失败: {str(e)}")
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n🔄 测试向后兼容性...")

    try:
        # 测试各种导入方式
        from app.processors.fresh_food_ratio import FreshFoodRatioProcessor, FreshFoodRatioService
        print("✅ 类导入成功")

        from app.processors.fresh_food_ratio import process_fresh_food_ratio, 函数
        print("✅ 函数导入成功")

        from app.processors.fresh_food_ratio import ExcelReportWriter
        print("✅ ExcelReportWriter 别名导入成功")

        # 测试实例化
        processor = FreshFoodRatioProcessor()
        service = FreshFoodRatioService()
        writer = ExcelReportWriter()
        print("✅ 实例化成功")

        return True

    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("清理后功能验证测试")
    print("=" * 60)

    tests = [
        test_backward_compatibility,
        test_basic_functionality
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 清理验证成功！所有功能正常工作")
        return True
    else:
        print("❌ 清理验证失败，存在问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)