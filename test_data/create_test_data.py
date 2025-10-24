#!/usr/bin/env python3
"""
生成测试用的Excel数据文件
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

def create_test_data():
    """创建测试数据"""

    # 创建测试数据目录
    test_data_dir = Path("test_data")
    test_data_dir.mkdir(exist_ok=True)

    # 生成上个月的订单数据
    last_month_start = datetime(2024, 9, 1)
    last_month_end = datetime(2024, 9, 30)

    # 生成本月的订单数据
    this_month_start = datetime(2024, 10, 1)
    this_month_end = datetime(2024, 10, 31)

    # 客户和业务员数据
    customers = [
        '客户A', '客户B', '客户C', '客户D', '客户E',
        '客户F', '客户G', '客户H', '客户I', '客户J'
    ]

    salesmen = ['业务员甲', '业务员乙', '业务员丙', '业务员丁']

    categories = ['新鲜蔬菜', '鲜肉类', '豆制品', '水果类', '调味品']

    # 生成上个月数据
    last_month_data = []
    for i in range(150):  # 150条订单记录
        order_date = last_month_start + timedelta(
            days=np.random.randint(0, 30),
            hours=np.random.randint(8, 18)
        )

        customer = np.random.choice(customers)
        salesman = np.random.choice(salesmen)
        category = np.random.choice(categories, p=[0.4, 0.3, 0.2, 0.07, 0.03])  # 生鲜占比较高

        # 生成金额，生鲜类金额较高
        if category in ['新鲜蔬菜', '鲜肉类', '豆制品']:
            amount = np.random.uniform(500, 5000)
        else:
            amount = np.random.uniform(100, 1000)

        last_month_data.append({
            '客户名称': customer,
            '业务员': salesman,
            '发货时间': order_date,
            '实际金额': round(amount, 2),
            '一级分类': category,
            '订单号': f'LM{10000 + i}'
        })

    # 生成本月数据
    this_month_data = []
    for i in range(180):  # 180条订单记录
        order_date = this_month_start + timedelta(
            days=np.random.randint(0, 31),
            hours=np.random.randint(8, 18)
        )

        customer = np.random.choice(customers)
        salesman = np.random.choice(salesmen)
        category = np.random.choice(categories, p=[0.45, 0.35, 0.15, 0.03, 0.02])  # 本月生鲜比例提升

        # 本月金额略高，体现业务增长
        if category in ['新鲜蔬菜', '鲜肉类', '豆制品']:
            amount = np.random.uniform(600, 6000)
        else:
            amount = np.random.uniform(120, 1200)

        this_month_data.append({
            '客户名称': customer,
            '业务员': salesman,
            '发货时间': order_date,
            '实际金额': round(amount, 2),
            '一级分类': category,
            '订单号': f'TM{20000 + i}'
        })

    # 创建DataFrame
    last_month_df = pd.DataFrame(last_month_data)
    this_month_df = pd.DataFrame(this_month_data)

    # 保存为Excel文件
    last_month_file = test_data_dir / "2024年9月订单数据.xlsx"
    this_month_file = test_data_dir / "2024年10月订单数据.xlsx"

    with pd.ExcelWriter(last_month_file, engine='openpyxl') as writer:
        last_month_df.to_excel(writer, sheet_name='订单数据', index=False)

    with pd.ExcelWriter(this_month_file, engine='openpyxl') as writer:
        this_month_df.to_excel(writer, sheet_name='订单数据', index=False)

    print(f"测试数据已生成:")
    print(f"- 上月数据: {last_month_file}")
    print(f"- 本月数据: {this_month_file}")
    print(f"- 上月订单数: {len(last_month_df)}")
    print(f"- 本月订单数: {len(this_month_df)}")

    # 验证数据完整性
    print("\n数据验证:")
    print(f"上月生鲜订单: {len(last_month_df[last_month_df['一级分类'].isin(['新鲜蔬菜', '鲜肉类', '豆制品'])])}")
    print(f"本月生鲜订单: {len(this_month_df[this_month_df['一级分类'].isin(['新鲜蔬菜', '鲜肉类', '豆制品'])])}")

    return str(last_month_file), str(this_month_file)

if __name__ == "__main__":
    create_test_data()