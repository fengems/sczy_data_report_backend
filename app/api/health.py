"""
健康检查API
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("health")


@router.get("/health", summary="健康检查")
async def health_check() -> Dict[str, Any]:
    """检查服务健康状态"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SCZY数据报告系统",
        "version": "1.0.0"
    }


@router.get("/ping", summary="Ping检查")
async def ping() -> Dict[str, str]:
    """简单的ping检查"""
    logger.info("Ping request received")
    return {"message": "pong"}