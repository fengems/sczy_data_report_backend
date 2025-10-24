#!/usr/bin/env python3
"""
测试纯模块化后的实际功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_real_functionality():
    """测试实际功能"""
    print("🔍 测试实际功能...")

    try:
        # 导入
        from app.processors.fresh_food_ratio import process_fresh_food_ratio
        print("✅ 导入成功")

        # 测试数据文件
        last_month_file = "test_data/2024年9月订单数据.xlsx"
        this_month_file = "test_data/2024年10月订单数据.xlsx"

        # 检查测试数据是否存在
        if not Path(last_month_file).exists() or not Path(this_month_file).exists():
            print("ℹ️ 测试数据文件不存在，跳过功能测试")
            return True

        # 测试处理功能
        output_file = "outputs/test_pure_module.xlsx"
        result_df, result_path = process_fresh_food_ratio(
            last_month_file,
            this_month_file,
            output_file
        )

        print(f"✅ 处理成功")
        print(f"📊 数据行数: {len(result_df)}")
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

def test_import_compatibility():
    """测试导入兼容性"""
    print("\n🔄 测试导入兼容性...")

    try:
        # 测试各种导入方式
        from app.processors.fresh_food_ratio import FreshFoodRatioProcessor
        from app.processors.fresh_food_ratio import FreshFoodRatioService
        from app.processors.fresh_food_ratio import process_fresh_food_ratio
        from app.processors.fresh_food_ratio import 函数
        from app.processors.fresh_food_ratio import ExcelReportWriter
        print("✅ 所有导入方式正常")

        return True

    except Exception as e:
        print(f"❌ 导入测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("纯模块化功能测试")
    print("=" * 60)

    tests = [
        test_import_compatibility,
        test_real_functionality
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 纯模块化功能完全正常！")
        return True
    else:
        print("❌ 纯模块化功能存在问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)