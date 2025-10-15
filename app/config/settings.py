"""
应用配置管理模块
"""
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基础配置
    app_name: str = Field(default="SCZY数据报告系统", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    host: str = Field(default="0.0.0.0", description="服务主机")
    port: int = Field(default=8000, description="服务端口")

    # ERP系统配置
    erp_base_url: str = Field(..., description="ERP系统基础URL")
    erp_username: str = Field(..., description="ERP用户名")
    erp_password: str = Field(..., description="ERP密码")
    erp_login_page: str = Field(default="/login", description="ERP登录页面路径")

    # 浏览器配置
    browser_headless: bool = Field(default=True, description="无头浏览器模式")
    browser_timeout: int = Field(default=30000, description="浏览器超时时间(毫秒)")
    browser_download_path: str = Field(default="./downloads", description="浏览器下载路径")

    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis连接URL")

    # Celery配置
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery代理URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", description="Celery结果后端")

    # 企业微信配置
    wechat_webhook: Optional[str] = Field(default=None, description="企业微信Webhook地址")

    # 文件存储配置
    upload_path: str = Field(default="./uploads", description="上传文件路径")
    output_path: str = Field(default="./outputs", description="输出文件路径")
    temp_path: str = Field(default="./temp", description="临时文件路径")

    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="./logs/app.log", description="日志文件路径")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.browser_download_path,
            self.upload_path,
            self.output_path,
            self.temp_path,
            Path(self.log_file).parent,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()