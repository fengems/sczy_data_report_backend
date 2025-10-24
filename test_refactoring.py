#!/usr/bin/env python3
"""
测试重构后的生鲜环比功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有导入是否正常"""
    print("🔍 测试导入...")

    try:
        # 测试新的模块导入
        from app.processors.utils.base_excel_processor import BaseExcelProcessor
        print("✅ BaseExcelProcessor 导入成功")

        from app.outputs.utils.base_excel_writer import BaseExcelWriter
        print("✅ BaseExcelWriter 导入成功")

        from app.processors.fresh_food_ratio.processor import FreshFoodRatioProcessor
        print("✅ FreshFoodRatioProcessor 导入成功")

        from app.outputs.fresh_food_ratio.writer import FreshFoodRatioExcelWriter
        print("✅ FreshFoodRatioExcelWriter 导入成功")

        from app.processors.fresh_food_ratio.service import FreshFoodRatioService
        print("✅ FreshFoodRatioService 导入成功")

        # 测试向后兼容的导入
        from app.processors.fresh_food_ratio import process_fresh_food_ratio, 函数
        print("✅ 便捷函数导入成功")

        from app.processors.fresh_food_ratio import FreshFoodRatioProcessor as OldProcessor
        print("✅ 向后兼容导入成功")

        from app.processors.fresh_food_ratio import ExcelReportWriter
        print("✅ ExcelReportWriter 别名导入成功")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False

def test_instantiation():
    """测试类实例化"""
    print("\n🏗️ 测试类实例化...")

    try:
        from app.processors.fresh_food_ratio.processor import FreshFoodRatioProcessor
        from app.outputs.fresh_food_ratio.writer import FreshFoodRatioExcelWriter
        from app.processors.fresh_food_ratio.service import FreshFoodRatioService

        processor = FreshFoodRatioProcessor()
        print("✅ FreshFoodRatioProcessor 实例化成功")

        writer = FreshFoodRatioExcelWriter()
        print("✅ FreshFoodRatioExcelWriter 实例化成功")

        service = FreshFoodRatioService()
        print("✅ FreshFoodRatioService 实例化成功")

        return True

    except Exception as e:
        print(f"❌ 实例化失败: {str(e)}")
        return False

def test_inheritance():
    """测试继承关系"""
    print("\n🧬 测试继承关系...")

    try:
        from app.processors.utils.base_excel_processor import BaseExcelProcessor
        from app.processors.fresh_food_ratio.processor import FreshFoodRatioProcessor

        from app.outputs.utils.base_excel_writer import BaseExcelWriter
        from app.outputs.fresh_food_ratio.writer import FreshFoodRatioExcelWriter

        # 测试继承关系
        assert issubclass(FreshFoodRatioProcessor, BaseExcelProcessor)
        print("✅ FreshFoodRatioProcessor 正确继承 BaseExcelProcessor")

        assert issubclass(FreshFoodRatioExcelWriter, BaseExcelWriter)
        print("✅ FreshFoodRatioExcelWriter 正确继承 BaseExcelWriter")

        return True

    except Exception as e:
        print(f"❌ 继承关系测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("生鲜环比重构验证测试")
    print("=" * 60)

    tests = [
        test_imports,
        test_instantiation,
        test_inheritance
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 重构验证成功！所有功能正常工作")
        return True
    else:
        print("❌ 重构验证失败，需要修复问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)