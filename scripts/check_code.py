#!/usr/bin/env python3
"""
代码质量检查脚本
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print("✅ 通过")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print("❌ 失败")
            if result.stderr.strip():
                print("错误信息:", result.stderr)
            if result.stdout.strip():
                print("输出:", result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始代码质量检查...")

    # 切换到项目根目录
    project_root = Path(__file__).parent
    import os
    os.chdir(project_root)

    all_passed = True

    # 1. Black 格式检查（仅检查，不修改）
    all_passed &= run_command("black --check app/", "Black 格式检查")

    # 2. isort 导入排序检查（仅检查，不修改）
    all_passed &= run_command("isort --check-only app/", "isort 导入排序检查")

    # 3. Flake8 代码风格检查
    all_passed &= run_command("flake8 app/ --max-complexity=25 --extend-ignore=C901", "Flake8 代码风格检查")

    # 4. MyPy 类型检查
    all_passed &= run_command("mypy app/ --ignore-missing-imports --no-strict-optional", "MyPy 类型检查")

    print("\n" + "="*50)
    if all_passed:
        print("🎉 所有代码质量检查都通过了！")
        return 0
    else:
        print("❌ 有检查失败，请修复上述问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())