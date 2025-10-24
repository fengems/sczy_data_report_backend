#!/usr/bin/env python3
"""
生鲜环比功能测试脚本
用于验证Excel处理模块的功能
"""

import sys
import os
import logging
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.processors.fresh_food_ratio import process_fresh_food_ratio, 函数

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fresh_food_ratio_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def create_test_data():
    """创建测试数据"""
    logger.info("正在创建测试数据...")

    # 创建测试目录
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)

    # 生成上个月测试数据
    last_month_data = {
        '客户名称': ['客户A', '客户B', '客户C', '客户A', '客户B'] * 10,
        '业务员': ['业务员1', '业务员2', '业务员1', '业务员1', '业务员2'] * 10,
        '发货时间': pd.date_range('2024-09-01', periods=50, freq='D'),
        '实际金额': [100, 200, 150, 120, 180] * 10,
        '一级分类': ['新鲜蔬菜', '鲜肉类', '豆制品', '新鲜蔬菜', '鲜肉类'] * 10
    }
    last_month_df = pd.DataFrame(last_month_data)
    last_month_file = test_dir / "订单导出_9月.xlsx"
    last_month_df.to_excel(last_month_file, index=False)

    # 生成本月测试数据
    this_month_data = {
        '客户名称': ['客户A', '客户B', '客户C', '客户D', '客户A', '客户B'] * 10,
        '业务员': ['业务员1', '业务员2', '业务员1', '业务员3', '业务员1', '业务员2'] * 10,
        '发货时间': pd.date_range('2024-10-01', periods=60, freq='D'),
        '实际金额': [120, 220, 160, 200, 140, 190] * 10,
        '一级分类': ['新鲜蔬菜', '鲜肉类', '豆制品', '新鲜蔬菜', '鲜肉类', '豆制品'] * 10
    }
    this_month_df = pd.DataFrame(this_month_data)
    this_month_file = test_dir / "订单导出_10月至今.xlsx"
    this_month_df.to_excel(this_month_file, index=False)

    logger.info(f"测试数据创建完成:")
    logger.info(f"上月文件: {last_month_file}")
    logger.info(f"本月文件: {this_month_file}")

    return str(last_month_file), str(this_month_file)


def test_with_real_files():
    """使用真实文件测试"""
    logger.info("=== 使用真实文件测试 ===")

    # 检查downloads目录中是否有测试文件
    downloads_dir = Path("downloads")
    last_month_files = list(downloads_dir.glob("*9月*.xlsx"))
    this_month_files = list(downloads_dir.glob("*10月*.xlsx"))

    if not last_month_files:
        logger.warning("未找到9月订单文件")
        return False

    if not this_month_files:
        logger.warning("未找到10月订单文件")
        return False

    last_month_file = last_month_files[0]
    this_month_file = this_month_files[0]

    logger.info(f"使用文件:")
    logger.info(f"上月: {last_month_file}")
    logger.info(f"本月: {this_month_file}")

    try:
        # 测试处理函数
        result_df, output_path = process_fresh_food_ratio(
            str(last_month_file),
            str(this_month_file)
        )

        logger.info(f"处理成功! 结果数据形状: {result_df.shape}")
        logger.info(f"输出文件: {output_path}")
        logger.info("\n结果预览:")
        logger.info(result_df.head().to_string())

        return True

    except Exception as e:
        logger.error(f"真实文件测试失败: {str(e)}")
        return False


def test_with_mock_data():
    """使用模拟数据测试"""
    logger.info("=== 使用模拟数据测试 ===")

    try:
        # 创建测试数据
        last_month_file, this_month_file = create_test_data()

        # 测试处理函数
        result_df, output_path = process_fresh_food_ratio(
            last_month_file,
            this_month_file
        )

        logger.info(f"处理成功! 结果数据形状: {result_df.shape}")
        logger.info(f"输出文件: {output_path}")
        logger.info("\n结果预览:")
        logger.info(result_df.head().to_string())

        # 验证关键列是否存在
        required_columns = [
            '客户名称', '业务员', '本月总日活', '上月总日活', '总日活环比',
            '本月新鲜蔬菜销售额', '上月新鲜蔬菜销售额', '蔬菜销售额环比',
            '本月鲜肉类销售额', '上月鲜肉类销售额', '鲜肉销售额环比',
            '本月豆制品销售额', '上月豆制品销售额', '豆制品销售额环比',
            '本月生鲜销售额', '上月生鲜销售额', '生鲜销售额环比'
        ]

        missing_columns = [col for col in required_columns if col not in result_df.columns]
        if missing_columns:
            logger.error(f"缺少必要的列: {missing_columns}")
            return False

        logger.info("所有必要的列都存在")
        return True

    except Exception as e:
        logger.error(f"模拟数据测试失败: {str(e)}")
        return False


def test_chinese_function():
    """测试中文函数名"""
    logger.info("=== 测试中文函数名 ===")

    try:
        # 创建测试数据
        last_month_file, this_month_file = create_test_data()

        # 使用中文函数名测试
        result_df, output_path = 函数(last_month_file, this_month_file)

        logger.info(f"中文函数测试成功! 结果数据形状: {result_df.shape}")
        logger.info(f"输出文件: {output_path}")

        return True

    except Exception as e:
        logger.error(f"中文函数测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    logger.info("开始生鲜环比功能测试...")

    test_results = []

    # 测试1: 模拟数据测试
    logger.info("\n" + "="*50)
    test_results.append(test_with_mock_data())

    # 测试2: 中文函数名测试
    logger.info("\n" + "="*50)
    test_results.append(test_chinese_function())

    # 测试3: 真实文件测试（如果文件存在）
    logger.info("\n" + "="*50)
    test_results.append(test_with_real_files())

    # 汇总测试结果
    logger.info("\n" + "="*50)
    logger.info("=== 测试结果汇总 ===")
    test_names = ["模拟数据测试", "中文函数测试", "真实文件测试"]

    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{i+1}. {name}: {status}")

    total_passed = sum(test_results)
    total_tests = len(test_results)

    logger.info(f"\n总计: {total_passed}/{total_tests} 个测试通过")

    if total_passed == total_tests:
        logger.info("🎉 所有测试都通过了!")
        return 0
    else:
        logger.error("❌ 有测试失败，请检查日志")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)