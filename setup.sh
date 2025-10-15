#!/bin/bash

# SCZY ERP数据爬取系统环境设置脚本

echo "🔧 设置SCZY ERP数据爬取系统环境..."

# 检查Python版本
echo "🐍 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python版本: $PYTHON_VERSION"

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ -d "venv" ]; then
    echo "⚠️  虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装项目依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

# 安装Playwright浏览器
echo "🌐 安装Playwright浏览器..."
playwright install chromium

# 创建配置文件
if [ ! -f ".env" ]; then
    echo "📝 创建配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置你的ERP系统信息"
fi

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p logs uploads downloads outputs temp

# 验证安装
echo "🔍 验证安装..."
python -c "
try:
    import fastapi, uvicorn, playwright, pandas, openpyxl
    print('✅ 所有核心依赖导入成功')
except ImportError as e:
    print(f'❌ 依赖导入失败: {e}')
    exit(1)

try:
    from app.config.settings import settings
    print(f'✅ 配置模块加载成功: {settings.app_name}')
except ImportError as e:
    print(f'❌ 配置模块加载失败: {e}')
    exit(1)
"

echo ""
echo "🎉 环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 编辑 .env 文件配置你的ERP系统信息"
echo "2. 运行 ./start.sh 启动服务"
echo "3. 访问 http://localhost:8000/docs 查看API文档"
echo ""