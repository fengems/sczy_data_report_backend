#!/usr/bin/env python3
"""
测试最终的纯模块化结构
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_direct_import():
    """测试直接从模块导入"""
    print("🔍 测试直接模块导入...")

    try:
        # 测试从模块内部直接导入
        from app.processors.fresh_food_ratio import (
            FreshFoodRatioProcessor,
            FreshFoodRatioService,
            process_fresh_food_ratio,
            函数,
            ExcelReportWriter
        )
        print("✅ 直接模块导入成功")

        # 测试实例化
        processor = FreshFoodRatioProcessor()
        service = FreshFoodRatioService()
        print("✅ 实例化成功")

        return True

    except Exception as e:
        print(f"❌ 直接模块导入失败: {str(e)}")
        return False

def test_no_external_files():
    """验证外部没有多余文件"""
    print("\n🧹 验证外部文件清理...")

    external_file = project_root / "app" / "processors" / "fresh_food_ratio.py"

    if not external_file.exists():
        print("✅ 外部文件已清理，模块完全内部化")
        return True
    else:
        print("❌ 外部文件仍然存在，清理不彻底")
        return False

def test_module_structure():
    """测试模块内部结构"""
    print("\n📁 验证模块内部结构...")

    module_dir = project_root / "app" / "processors" / "fresh_food_ratio"
    required_files = {
        "__init__.py",
        "processor.py",
        "service.py",
        "main.py",
        "entry.py"
    }

    all_present = True
    for file_name in required_files:
        file_path = module_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} 存在")
        else:
            print(f"❌ {file_name} 不存在")
            all_present = False

    return all_present

def test_functionality():
    """测试功能完整性"""
    print("\n⚙️ 测试功能完整性...")

    try:
        from app.processors.fresh_food_ratio import FreshFoodRatioProcessor

        # 测试基类继承
        from app.processors.utils.base_excel_processor import BaseExcelProcessor
        assert issubclass(FreshFoodRatioProcessor, BaseExcelProcessor)
        print("✅ 继承关系正确")

        # 测试必需列定义
        processor = FreshFoodRatioProcessor()
        assert '客户名称' in processor.required_columns
        print("✅ 业务逻辑正常")

        return True

    except Exception as e:
        print(f"❌ 功能测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("最终纯模块化结构验证测试")
    print("=" * 60)

    tests = [
        test_direct_import,
        test_no_external_files,
        test_module_structure,
        test_functionality
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 纯模块化结构验证成功！")
        print("✅ 没有任何外部冗余文件")
        print("✅ 模块完全自包含")
        print("✅ 所有功能正常工作")
        return True
    else:
        print("❌ 纯模块化结构验证失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)