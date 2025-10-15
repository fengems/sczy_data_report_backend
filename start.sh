#!/bin/bash

# SCZY ERP数据爬取系统启动脚本

echo "🚀 正在启动SCZY ERP数据爬取系统..."

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 setup.sh 创建环境"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env配置文件不存在，正在从模板创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件配置你的ERP系统信息"
fi

# 创建必要的目录
mkdir -p logs uploads downloads outputs temp

echo "🌐 启动FastAPI服务..."
echo "📖 API文档将在启动后可访问: http://localhost:8000/docs"
echo "🔍 健康检查: http://localhost:8000/api/v1/health"
echo "⏹️  按 Ctrl+C 停止服务"
echo ""

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000