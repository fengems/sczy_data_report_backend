#!/usr/bin/env python3
"""
生鲜环比数据处理模块测试脚本
测试 app/processors/fresh_food_ratio.py 的完整功能
"""

import logging
import sys
import tempfile
from pathlib import Path

import pytest
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.outputs.excel_writer import ExcelReportWriter
from app.processors.excel_processor import FreshFoodRatioProcessor
from app.processors.fresh_food_ratio import (
    FreshFoodRatioService,
    process_fresh_food_ratio,
    函数,
)
from app.utils.logger import get_logger

# 设置测试日志
logger = get_logger("test_fresh_food_ratio")
logging.basicConfig(level=logging.INFO)

# 测试数据路径
TEST_DATA_DIR = project_root / "test_data"
LAST_MONTH_FILE = TEST_DATA_DIR / "订单导出_9月.xlsx"
THIS_MONTH_FILE = TEST_DATA_DIR / "订单导出_10月至今.xlsx"


class TestFreshFoodRatioProcessor:
    """测试 FreshFoodRatioProcessor 类"""

    @pytest.fixture
    def processor(self):
        """创建处理器实例"""
        return FreshFoodRatioProcessor()

    @pytest.fixture
    def test_data(self):
        """确保测试数据存在"""
        if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
            pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")

        return str(LAST_MONTH_FILE), str(THIS_MONTH_FILE)

    def test_init(self, processor):
        """测试处理器初始化"""
        assert processor is not None
        assert hasattr(processor, "required_columns")
        assert "客户名称" in processor.required_columns
        assert "业务员" in processor.required_columns
        assert "发货时间" in processor.required_columns
        assert "实际金额" in processor.required_columns
        assert "一级分类" in processor.required_columns

    def test_validate_columns_success(self, processor):
        """测试列验证成功情况"""
        # 创建包含所有必要列的DataFrame
        df = pd.DataFrame(
            {
                "客户名称": ["客户A"],
                "业务员": ["业务员甲"],
                "发货时间": ["2024-10-01"],
                "实际金额": [1000],
                "一级分类": ["新鲜蔬菜"],
            }
        )

        result = processor.validate_columns(df, "test_file.xlsx")
        assert result is True

    def test_validate_columns_failure(self, processor):
        """测试列验证失败情况"""
        # 创建缺少必要列的DataFrame
        df = pd.DataFrame(
            {
                "客户名称": ["客户A"],
                "业务员": ["业务员甲"],
                # 缺少其他必要列
            }
        )

        result = processor.validate_columns(df, "test_file.xlsx")
        assert result is False

    def test_read_excel_file_success(self, processor, test_data):
        """测试成功读取Excel文件"""
        last_month_file, _ = test_data

        # 测试读取文件
        df = processor.read_excel_file(last_month_file)

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "客户名称" in df.columns
        assert "发货时间" in df.columns
        assert df["发货时间"].dtype.kind in ["M", "m"]  # 检查是否为datetime类型

    def test_read_excel_file_failure(self, processor):
        """测试读取不存在的文件"""
        with pytest.raises(Exception):
            processor.read_excel_file("nonexistent_file.xlsx")

    def test_merge_order_data(self, processor, test_data):
        """测试合并订单数据"""
        last_month_file, this_month_file = test_data

        # 读取数据
        last_df = processor.read_excel_file(last_month_file)
        this_df = processor.read_excel_file(this_month_file)

        # 合并数据
        merged = processor.merge_order_data(last_df, this_df)

        assert isinstance(merged, pd.DataFrame)
        assert "月份" in merged.columns
        # 数据经过筛选后，行数应该小于等于原始数据总和
        assert len(merged) <= len(last_df) + len(this_df)
        assert set(merged["月份"].unique()) == {"上月", "本月"}
        # 验证数据已按发货时间降序排序
        assert merged['发货时间'].is_monotonic_decreasing

    def test_calculate_order_days(self, processor, test_data):
        """测试计算下单天数"""
        last_month_file, this_month_file = test_data

        # 读取并合并数据
        last_df = processor.read_excel_file(last_month_file)
        this_df = processor.read_excel_file(this_month_file)
        merged = processor.merge_order_data(last_df, this_df)

        # 计算下单天数
        last_days, this_days = processor.calculate_order_days(merged)

        assert isinstance(last_days, int)
        assert isinstance(this_days, int)
        assert last_days > 0
        assert this_days > 0

    def test_create_pivot_table_base(self, processor, test_data):
        """测试创建基础透视表"""
        last_month_file, this_month_file = test_data

        # 读取并合并数据
        last_df = processor.read_excel_file(last_month_file)
        this_df = processor.read_excel_file(this_month_file)
        merged = processor.merge_order_data(last_df, this_df)

        # 创建透视表
        pivot = processor.create_pivot_table_base(merged)

        assert isinstance(pivot, pd.DataFrame)
        assert "客户名称" in pivot.columns
        assert "业务员" in pivot.columns
        # 验证每个客户只有一行（唯一客户名称）
        assert len(pivot) == len(pivot['客户名称'].unique())
        assert len(pivot) > 0

    def test_calculate_sales_data(self, processor, test_data):
        """测试计算销售数据"""
        last_month_file, this_month_file = test_data

        # 读取并合并数据
        last_df = processor.read_excel_file(last_month_file)
        this_df = processor.read_excel_file(this_month_file)
        merged = processor.merge_order_data(last_df, this_df)

        # 计算蔬菜销售数据
        veg_last, veg_this = processor.calculate_sales_data(merged, "新鲜蔬菜")

        assert isinstance(veg_last, pd.DataFrame)
        assert isinstance(veg_this, pd.DataFrame)
        assert "客户名称" in veg_last.columns
        assert "客户名称" in veg_this.columns
        assert "上月新鲜蔬菜销售额" in veg_last.columns
        assert "本月新鲜蔬菜销售额" in veg_this.columns

    def test_calculate_ratio(self, processor):
        """测试环比计算"""
        # 正常情况
        ratio = processor.calculate_ratio(120, 100)
        assert ratio == 20.0

        # 零除情况
        ratio = processor.calculate_ratio(100, 0)
        assert ratio == 0.0

        # 负增长情况
        ratio = processor.calculate_ratio(80, 100)
        assert ratio == -20.0

    def test_get_customer_diff_complete_flow(self, processor, test_data):
        """测试客户环比数据完整流程"""
        last_month_file, this_month_file = test_data

        # 执行完整流程
        result = processor.get_customer_diff(last_month_file, this_month_file)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

        # 检查必要的列是否存在（移除订单数量列）
        required_columns = [
            "客户名称",
            "业务员",
            "本月总日活",
            "上月总日活",
            "总日活环比",
            "本月新鲜蔬菜销售额",
            "上月新鲜蔬菜销售额",
            "蔬菜销售额环比",
            "本月鲜肉类销售额",
            "上月鲜肉类销售额",
            "鲜肉销售额环比",
            "本月豆制品销售额",
            "上月豆制品销售额",
            "豆制品销售额环比",
            "本月生鲜销售额",
            "上月生鲜销售额",
            "生鲜销售额环比",
        ]

        for col in required_columns:
            assert col in result.columns, f"缺少列: {col}"

        # 验证数据类型和值的合理性
        assert result["生鲜销售额环比"].dtype == float
        # 验证每个客户只有一行（唯一客户名称）
        assert len(result) == len(result['客户名称'].unique())
        logger.info(f"结果数据行数: {len(result)}")
        logger.info(f"唯一客户数: {len(result['客户名称'].unique())}")
        logger.info(f"唯一业务员数: {len(result['业务员'].unique())}")


class TestFreshFoodRatioService:
    """测试 FreshFoodRatioService 类"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        return FreshFoodRatioService()

    @pytest.fixture
    def test_data(self):
        """确保测试数据存在"""
        if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
            pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")

        return str(LAST_MONTH_FILE), str(THIS_MONTH_FILE)

    def test_init(self, service):
        """测试服务初始化"""
        assert service is not None
        assert hasattr(service, "processor")
        assert hasattr(service, "writer")
        assert isinstance(service.processor, FreshFoodRatioProcessor)
        assert isinstance(service.writer, ExcelReportWriter)

    def test_validate_input_files_success(self, service, test_data):
        """测试输入文件验证成功"""
        last_month_file, this_month_file = test_data

        # 应该不抛出异常
        service._validate_input_files(last_month_file, this_month_file)

    def test_validate_input_files_not_exist(self, service):
        """测试验证不存在的文件"""
        with pytest.raises(FileNotFoundError):
            service._validate_input_files("nonexistent1.xlsx", "nonexistent2.xlsx")

    def test_validate_input_files_wrong_format(self, service, test_data):
        """测试验证错误格式的文件"""
        last_month_file, _ = test_data

        # 创建临时文件但格式错误
        with tempfile.TemporaryDirectory() as temp_dir:
            wrong_format_file = Path(temp_dir) / "test.txt"
            wrong_format_file.write_text("这不是Excel文件")

            with pytest.raises(ValueError):
                service._validate_input_files(last_month_file, str(wrong_format_file))

    def test_process_fresh_food_ratio_complete_flow(self, service, test_data):
        """测试生鲜环比处理完整流程"""
        last_month_file, this_month_file = test_data

        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_output.xlsx"

            # 执行处理流程
            result_df, result_path = service.process_fresh_food_ratio(
                last_month_file, this_month_file, str(output_file)
            )

            # 验证结果
            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) > 0
            assert Path(result_path).exists()
            assert Path(result_path) == output_file

            # 验证输出Excel文件内容
            with pd.ExcelFile(result_path) as xls:
                assert "客户环比" in xls.sheet_names
                assert "数据摘要" in xls.sheet_names


class TestExcelReportWriter:
    """测试 ExcelReportWriter 类"""

    @pytest.fixture
    def writer(self):
        """创建写入器实例"""
        return ExcelReportWriter()

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return pd.DataFrame(
            {
                "客户名称": ["客户A", "客户B", "客户C"],
                "业务员": ["业务员甲", "业务员乙", "业务员丙"],
                "订单数量": [10, 15, 8],
                "本月总日活": [20, 25, 15],
                "上月总日活": [18, 22, 12],
                "总日活环比": [11.11, 13.64, 25.0],
                "本月生鲜销售额": [5000, 6000, 3000],
                "上月生鲜销售额": [4500, 5500, 2800],
                "生鲜销售额环比": [11.11, 9.09, 7.14],
            }
        )

    def test_init(self, writer):
        """测试写入器初始化"""
        assert writer is not None
        assert hasattr(writer, "default_output_dir")
        assert writer.default_output_dir.exists()

    def test_format_number(self, writer):
        """测试数字格式化"""
        # 普通数字
        assert writer.format_number(1234.56) == "1.23K"

        # 百万级数字
        assert writer.format_number(1234567) == "1.23M"

        # 小数字
        assert writer.format_number(123.45) == "123.45"

        # 零值
        assert writer.format_number(0) == "0"

        # 百分比格式
        assert writer.format_number(12.34, is_percentage=True) == "12.34%"

    def test_write_fresh_food_ratio_report(self, writer, sample_data):
        """测试写入生鲜环比报告"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_report.xlsx"

            # 写入报告
            result_path = writer.write_fresh_food_ratio_report(
                sample_data, str(output_file)
            )

            # 验证文件存在
            assert Path(result_path).exists()
            assert Path(result_path) == output_file

            # 验证文件内容
            with pd.ExcelFile(result_path) as xls:
                assert "客户环比" in xls.sheet_names
                assert "数据摘要" in xls.sheet_names

                # 验证客户环比数据（注意：由于增加了表头行，实际数据从第2行开始）
                customer_df = pd.read_excel(xls, sheet_name="客户环比", header=1)  # 跳过表头行，从第1行开始读取列名
                assert len(customer_df) == len(sample_data)
                assert "客户名称" in customer_df.columns


class TestConvenienceFunctions:
    """测试便捷函数"""

    @pytest.fixture
    def test_data(self):
        """确保测试数据存在"""
        if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
            pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")

        return str(LAST_MONTH_FILE), str(THIS_MONTH_FILE)

    def test_process_fresh_food_ratio_function(self, test_data):
        """测试 process_fresh_food_ratio 便捷函数"""
        last_month_file, this_month_file = test_data

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_convenience.xlsx"

            # 调用便捷函数
            result_df, result_path = process_fresh_food_ratio(
                last_month_file, this_month_file, str(output_file)
            )

            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) > 0
            assert Path(result_path).exists()

    def test_chinese_function(self, test_data):
        """测试中文命名函数"""
        last_month_file, this_month_file = test_data

        with tempfile.TemporaryDirectory() as temp_dir:
            # 调用中文函数
            result_df, result_path = 函数(last_month_file, this_month_file)

            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) > 0
            assert Path(result_path).exists()


class TestErrorHandling:
    """测试错误处理"""

    def test_empty_files(self):
        """测试空文件处理"""
        # 创建空Excel文件
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_file = Path(temp_dir) / "empty.xlsx"
            pd.DataFrame().to_excel(empty_file, index=False)

            processor = FreshFoodRatioProcessor()

            # 应该抛出异常
            with pytest.raises(Exception):
                processor.read_excel_file(str(empty_file))

    def test_missing_columns(self):
        """测试缺少必要列的情况"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建缺少列的Excel文件
            incomplete_file = Path(temp_dir) / "incomplete.xlsx"
            incomplete_data = pd.DataFrame(
                {
                    "客户名称": ["客户A"],
                    "业务员": ["业务员甲"],
                    # 缺少其他必要列
                }
            )
            incomplete_data.to_excel(incomplete_file, index=False)

            processor = FreshFoodRatioProcessor()

            # 应该抛出异常
            with pytest.raises(ValueError):
                processor.read_excel_file(str(incomplete_file))


def test_integration_complete_workflow():
    """集成测试：完整工作流程"""
    if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
        pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(temp_dir) / "integration_test.xlsx"

        logger.info("开始集成测试...")

        # 执行完整流程
        result_df, result_path = process_fresh_food_ratio(
            str(LAST_MONTH_FILE), str(THIS_MONTH_FILE), str(output_file)
        )

        logger.info(f"集成测试完成，输出文件: {result_path}")

        # 验证结果
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) > 0
        assert Path(result_path).exists()

        # 验证输出文件内容
        with pd.ExcelFile(result_path) as xls:
            sheets = xls.sheet_names
            assert "客户环比" in sheets
            assert "数据摘要" in sheets

            # 验证数据完整性
            customer_data = pd.read_excel(xls, sheet_name="客户环比")
            summary_data = pd.read_excel(xls, sheet_name="数据摘要")

            assert len(customer_data) > 0
            assert len(summary_data) > 0

            logger.info("集成测试验证通过")


if __name__ == "__main__":
    # 运行测试
    print("=" * 60)
    print("生鲜环比数据处理模块测试")
    print("=" * 60)

    # 检查测试数据
    if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
        print("❌ 测试数据文件不存在")
        print("请先运行: python test_data/create_test_data.py")
        sys.exit(1)

    print("✅ 测试数据已准备:")
    print(f"   - 上月数据: {LAST_MONTH_FILE}")
    print(f"   - 本月数据: {THIS_MONTH_FILE}")

    # 运行pytest
    print("\n🚀 开始运行测试...")
    print("-" * 60)

    # 运行特定测试
    test_file = __file__
    exit_code = pytest.main(
        [
            "-v",  # 详细输出
            test_file,
            "--tb=short",  # 简短的错误追踪
        ]
    )

    if exit_code == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n❌ 测试失败，退出码: {exit_code}")
        sys.exit(exit_code)
