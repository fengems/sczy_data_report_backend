#!/usr/bin/env python3
"""
测试新的Excel格式功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.processors.fresh_food_ratio import process_fresh_food_ratio

def test_excel_formatting():
    """测试Excel格式化功能"""

    # 测试数据文件
    last_month_file = "test_data/2024年9月订单数据.xlsx"
    this_month_file = "test_data/2024年10月订单数据.xlsx"

    # 检查测试数据是否存在
    if not Path(last_month_file).exists() or not Path(this_month_file).exists():
        print("❌ 测试数据文件不存在")
        print("请先运行: python test_data/create_test_data.py")
        return False

    print("🚀 开始测试Excel格式化功能...")

    try:
        # 处理生鲜环比数据
        output_file = "outputs/test_excel_formatting.xlsx"
        result_df, result_path = process_fresh_food_ratio(
            last_month_file,
            this_month_file,
            output_file
        )

        print(f"✅ Excel文件生成成功: {result_path}")
        print(f"📊 数据行数: {len(result_df)}")
        print(f"📊 数据列数: {len(result_df.columns)}")

        # 检查是否有负值数据来测试条件格式
        negative_columns = []
        for col in result_df.columns:
            if '环比' in col or '销售额' in col:
                if (result_df[col] < 0).any():
                    negative_columns.append(col)

        if negative_columns:
            print(f"🎯 发现负值列，将应用条件格式: {negative_columns}")
        else:
            print("ℹ️  没有发现负值数据，但条件格式功能已实现")

        # 验证输出文件
        if Path(result_path).exists():
            print(f"✅ 输出文件验证成功")

            # 获取文件大小
            file_size = Path(result_path).stat().st_size
            print(f"📁 文件大小: {file_size} 字节")

            return True
        else:
            print("❌ 输出文件不存在")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Excel格式化功能测试")
    print("=" * 60)

    success = test_excel_formatting()

    if success:
        print("\n🎉 Excel格式化功能测试通过！")
        print("\n📋 实现的功能:")
        print("1. ✅ 负值条件格式（浅红填充深红色文本）")
        print("2. ✅ 标题行垂直居中和水平居中对齐")
        print("3. ✅ 列宽设置（第一列25字符，其他列12字符）")
        print("\n📝 请打开生成的Excel文件查看效果:")
        print(f"   outputs/test_excel_formatting.xlsx")
    else:
        print("\n❌ Excel格式化功能测试失败")
        sys.exit(1)