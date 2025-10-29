#!/usr/bin/env python3
"""
生鲜环比数据处理模块优化测试脚本
使用缓存数据和优化fixture作用域，大幅提升测试速度
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

from app.processors.fresh_food_ratio import (
    FreshFoodRatioProcessor,
    FreshFoodRatioService,
    process_fresh_food_ratio,
    函数,
    ExcelReportWriter,
)
from app.utils.logger import get_logger

# 导入缓存管理器
sys.path.insert(0, str(project_root / "test_data"))
from cache_manager import TestDataManager

# 设置测试日志
logger = get_logger("test_fresh_food_ratio_optimized")
logging.basicConfig(level=logging.INFO)

# 测试数据路径
TEST_DATA_DIR = project_root / "test_data"
LAST_MONTH_FILE = TEST_DATA_DIR / "订单导出_9月.xlsx"
THIS_MONTH_FILE = TEST_DATA_DIR / "订单导出_10月至今.xlsx"


# =============================================================================
# 优化后的Fixture定义
# =============================================================================

@pytest.fixture(scope="session")
def processor():
    """会话级别的处理器实例，整个测试会话只创建一次"""
    return FreshFoodRatioProcessor()


@pytest.fixture(scope="session")
def excel_writer():
    """会话级别的Excel写入器实例"""
    return ExcelReportWriter()


@pytest.fixture(scope="module")
def cached_test_data():
    """
    模块级别的缓存数据，整个测试模块只加载一次
    这是性能优化的核心！
    """
    manager = TestDataManager()
    cache_data = manager.load_cache()

    # 验证缓存数据的完整性
    assert 'processor' in cache_data, "缓存数据缺少processor"
    assert 'last_df' in cache_data, "缓存数据缺少last_df"
    assert 'this_df' in cache_data, "缓存数据缺少this_df"
    assert 'merged' in cache_data, "缓存数据缺少merged"
    assert 'pivot' in cache_data, "缓存数据缺少pivot"
    assert 'sales_data' in cache_data, "缓存数据缺少sales_data"

    logger.info(f"✅ 缓存数据加载成功 - 合并数据: {len(cache_data['merged']):,} 行")
    return cache_data


@pytest.fixture(scope="module")
def test_data_files():
    """测试文件路径fixture，保持向后兼容"""
    if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
        pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")
    return str(LAST_MONTH_FILE), str(THIS_MONTH_FILE)


@pytest.fixture
def sample_dataframe():
    """创建示例DataFrame用于基础测试"""
    return pd.DataFrame({
        "客户名称": ["客户A", "客户B", "客户C"],
        "业务员": ["业务员甲", "业务员乙", "业务员丙"],
        "发货时间": pd.to_datetime(["2024-10-01", "2024-10-02", "2024-10-03"]),
        "实际金额": [1000.0, 1500.0, 800.0],
        "一级分类": ["新鲜蔬菜", "鲜肉类", "豆制品"],
    })


# =============================================================================
# 优化后的测试类
# =============================================================================

class TestFreshFoodRatioProcessorOptimized:
    """测试 FreshFoodRatioProcessor 类 - 优化版本"""

    def test_init(self, processor):
        """测试处理器初始化"""
        assert processor is not None
        assert hasattr(processor, "required_columns")
        assert "客户名称" in processor.required_columns
        assert "业务员" in processor.required_columns
        assert "发货时间" in processor.required_columns
        assert "实际金额" in processor.required_columns
        assert "一级分类" in processor.required_columns

    def test_validate_columns_success(self, processor, sample_dataframe):
        """测试列验证成功情况"""
        result = processor.validate_columns(sample_dataframe, "test_file.xlsx")
        assert result is True

    def test_validate_columns_failure(self, processor, sample_dataframe):
        """测试列验证失败情况"""
        # 创建缺少必要列的DataFrame
        incomplete_df = pd.DataFrame({
            "客户名称": ["客户A"],
            "业务员": ["业务员甲"],
        })

        result = processor.validate_columns(incomplete_df, "test_file.xlsx")
        assert result is False

    def test_cached_data_structure(self, cached_test_data):
        """测试缓存数据的结构完整性"""
        cache_data = cached_test_data

        # 验证所有必要的缓存数据存在
        required_keys = ['processor', 'last_df', 'this_df', 'merged', 'pivot', 'sales_data', 'order_days']
        for key in required_keys:
            assert key in cache_data, f"缓存数据缺少: {key}"

        # 验证数据质量
        assert len(cache_data['merged']) > 0, "合并数据为空"
        assert len(cache_data['pivot']) > 0, "透视表数据为空"
        assert len(cache_data['sales_data']) > 0, "销售数据为空"

        logger.info(f"缓存验证通过 - 合并数据: {len(cache_data['merged'])} 行")

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

    def test_cached_pivot_table(self, cached_test_data):
        """测试缓存的透视表数据"""
        pivot = cached_test_data['pivot']

        assert isinstance(pivot, pd.DataFrame)
        assert "客户名称" in pivot.columns
        # 注意：重构后的透视表可能不包含业务员列，这取决于业务逻辑
        assert len(pivot) > 0
        assert len(pivot) == len(pivot["客户名称"].unique())

    def test_cached_sales_data(self, cached_test_data):
        """测试缓存的销售数据"""
        sales_data = cached_test_data['sales_data']

        # 验证主要分类的销售数据
        categories = ["新鲜蔬菜", "鲜肉类", "豆制品"]
        for category in categories:
            assert category in sales_data, f"缺少分类: {category}"
            assert 'last_month' in sales_data[category], f"{category} 缺少上月数据"
            assert 'this_month' in sales_data[category], f"{category} 缺少本月数据"

            last_month_df = sales_data[category]['last_month']
            this_month_df = sales_data[category]['this_month']

            assert isinstance(last_month_df, pd.DataFrame), f"{category} 上月数据不是DataFrame"
            assert isinstance(this_month_df, pd.DataFrame), f"{category} 本月数据不是DataFrame"

    def test_cached_order_days(self, cached_test_data):
        """测试缓存的下单天数"""
        order_days = cached_test_data['order_days']

        assert 'last_month' in order_days
        assert 'this_month' in order_days
        assert isinstance(order_days['last_month'], int)
        assert isinstance(order_days['this_month'], int)
        assert order_days['last_month'] > 0
        assert order_days['this_month'] > 0

    def test_get_customer_diff_with_cached_data(self, cached_test_data, test_data_files):
        """使用缓存数据测试客户环比完整流程"""
        processor = cached_test_data['processor']
        last_month_file, this_month_file = test_data_files

        # 执行完整流程（但会复用缓存数据）
        result = processor.get_customer_diff(last_month_file, this_month_file)

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

        # 验证必要的列存在
        required_columns = [
            "客户名称", "业务员", "本月总日活", "上月总日活", "总日活环比",
            "本月新鲜蔬菜销售额", "上月新鲜蔬菜销售额", "蔬菜销售额环比",
            "本月鲜肉类销售额", "上月鲜肉类销售额", "鲜肉销售额环比",
            "本月豆制品销售额", "上月豆制品销售额", "豆制品销售额环比",
            "本月生鲜销售额", "上月生鲜销售额", "生鲜销售额环比",
        ]

        for col in required_columns:
            assert col in result.columns, f"缺少列: {col}"

        assert result["生鲜销售额环比"].dtype == float
        assert len(result) == len(result["客户名称"].unique())


class TestFreshFoodRatioServiceOptimized:
    """测试 FreshFoodRatioService 类 - 优化版本"""

    @pytest.fixture(scope="session")
    def service(self):
        """会话级别的服务实例"""
        return FreshFoodRatioService()

    def test_init(self, service):
        """测试服务初始化"""
        assert service is not None
        assert hasattr(service, "processor")
        assert hasattr(service, "writer")
        assert isinstance(service.processor, FreshFoodRatioProcessor)
        assert isinstance(service.writer, ExcelReportWriter)

    def test_validate_input_files_success(self, service, test_data_files):
        """测试输入文件验证成功"""
        last_month_file, this_month_file = test_data_files
        service._validate_input_files(last_month_file, this_month_file)  # 应该不抛出异常

    def test_validate_input_files_not_exist(self, service):
        """测试验证不存在的文件"""
        with pytest.raises(FileNotFoundError):
            service._validate_input_files("nonexistent1.xlsx", "nonexistent2.xlsx")

    def test_process_fresh_food_ratio_with_cached_data(self, service, cached_test_data, test_data_files):
        """使用缓存数据测试完整处理流程"""
        last_month_file, this_month_file = test_data_files

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_output_optimized.xlsx"

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


class TestExcelReportWriterOptimized:
    """测试 ExcelReportWriter 类 - 优化版本"""

    @pytest.fixture
    def writer(self, excel_writer):
        """使用会话级别的写入器实例"""
        return excel_writer

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return pd.DataFrame({
            "客户名称": ["客户A", "客户B", "客户C"],
            "业务员": ["业务员甲", "业务员乙", "业务员丙"],
            "本月总日活": [20, 25, 15],
            "上月总日活": [18, 22, 12],
            "总日活环比": [11.11, 13.64, 25.0],
            "本月生鲜销售额": [5000, 6000, 3000],
            "上月生鲜销售额": [4500, 5500, 2800],
            "生鲜销售额环比": [11.11, 9.09, 7.14],
        })

    def test_init(self, writer):
        """测试写入器初始化"""
        assert writer is not None
        assert hasattr(writer, "default_output_dir")
        assert writer.default_output_dir.exists()

    def test_format_number(self, writer):
        """测试数字格式化"""
        assert writer.format_number(1234.56) == "1.23K"
        assert writer.format_number(1234567) == "1.23M"
        assert writer.format_number(123.45) == "123.45"
        assert writer.format_number(0) == "0"
        assert writer.format_number(12.34, is_percentage=True) == "12.34%"

    def test_write_fresh_food_ratio_report(self, writer, sample_data):
        """测试写入生鲜环比报告"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_report_optimized.xlsx"

            # 写入报告
            result_path = writer.write_report(
                sample_data, output_file=str(output_file)
            )

            # 验证文件存在
            assert Path(result_path).exists()
            assert Path(result_path) == output_file

            # 验证文件内容
            with pd.ExcelFile(result_path) as xls:
                assert "客户环比" in xls.sheet_names
                assert "数据摘要" in xls.sheet_names

                # 验证客户环比数据
                customer_df = pd.read_excel(xls, sheet_name="客户环比", header=1)
                assert len(customer_df) == len(sample_data)
                assert "客户名称" in customer_df.columns


class TestConvenienceFunctionsOptimized:
    """测试便捷函数 - 优化版本"""

    @pytest.fixture
    def test_data_files(self):
        """确保测试数据存在"""
        if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
            pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")
        return str(LAST_MONTH_FILE), str(THIS_MONTH_FILE)

    def test_process_fresh_food_ratio_function(self, test_data_files):
        """测试 process_fresh_food_ratio 便捷函数"""
        last_month_file, this_month_file = test_data_files

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_convenience_optimized.xlsx"

            # 调用便捷函数
            result_df, result_path = process_fresh_food_ratio(
                last_month_file, this_month_file, str(output_file)
            )

            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) > 0
            assert Path(result_path).exists()

    def test_chinese_function(self, test_data_files):
        """测试中文命名函数"""
        last_month_file, this_month_file = test_data_files

        with tempfile.TemporaryDirectory() as temp_dir:
            # 调用中文函数
            result_df, result_path = 函数(last_month_file, this_month_file)

            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) > 0
            assert Path(result_path).exists()


def test_integration_complete_workflow_optimized():
    """集成测试：完整工作流程 - 优化版本"""
    if not LAST_MONTH_FILE.exists() or not THIS_MONTH_FILE.exists():
        pytest.skip("测试数据文件不存在，请先运行 test_data/create_test_data.py")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(temp_dir) / "integration_test_optimized.xlsx"

        logger.info("开始优化版集成测试...")

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

        logger.info("✅ 优化版集成测试验证通过")


def test_cache_performance():
    """缓存性能测试"""
    import time

    manager = TestDataManager()

    # 测试缓存创建时间
    start_time = time.time()
    cache_data = manager.create_cache()
    creation_time = time.time() - start_time

    # 测试缓存加载时间
    start_time = time.time()
    loaded_data = manager.load_cache()
    load_time = time.time() - start_time

    # 验证数据一致性
    assert len(cache_data['merged']) == len(loaded_data['merged'])
    assert len(cache_data['pivot']) == len(loaded_data['pivot'])

    print(f"\n🚀 缓存性能测试结果:")
    print(f"  创建时间: {creation_time:.2f} 秒")
    print(f"  加载时间: {load_time:.4f} 秒")
    print(f"  性能提升: {creation_time/load_time:.1f}x")
    print(f"  缓存大小: {manager.get_cache_info()['cache_size_mb']} MB")

    # 加载时间应该远小于创建时间
    assert load_time < creation_time / 10, "缓存加载时间不够快"


if __name__ == "__main__":
    # 运行优化测试
    print("=" * 60)
    print("生鲜环比数据处理模块优化测试")
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
    print("\n🚀 开始运行优化测试...")
    print("-" * 60)

    # 运行特定测试
    test_file = __file__
    exit_code = pytest.main([
        "-v",  # 详细输出
        test_file,
        "--tb=short",  # 简短的错误追踪
    ])

    if exit_code == 0:
        print("\n🎉 所有优化测试通过！")
    else:
        print(f"\n❌ 测试失败，退出码: {exit_code}")
        sys.exit(exit_code)