#!/bin/bash

echo "🔧 开始自动修复代码质量问题..."

# 1. 首先用 Black 格式化所有代码
echo "1. 运行 Black 格式化..."
black app/

# 2. 然后用 isort 排序导入
echo "2. 运行 isort 导入排序..."
isort app/

# 3. 再次运行 Black 确保 Black 和 isort 协调
echo "3. 再次运行 Black 确保格式一致..."
black app/

echo "✅ 自动修复完成！"
echo ""
echo "📋 现在运行手动检查剩余问题："

# 4. 检查剩余的问题
echo "=== Flake8 检查 ==="
flake8 app/ --max-complexity=25 --extend-ignore=C901

echo ""
echo "=== MyPy 类型检查 ==="
mypy app/ --ignore-missing-imports --no-strict-optional

echo ""
echo "💡 提示："
echo "- Flake8 的问题通常是行长度或代码风格问题"
echo "- MyPy 的问题是类型注解缺失"
echo "- 这些需要手动修复"