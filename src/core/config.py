"""
ماژول پیکربندی

این ماژول تنظیمات برنامه را از متغیرهای محیطی بارگذاری می‌کند.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    کلاس تنظیمات برنامه
    """
    # تنظیمات عمومی
    app_name: str = "Anti-Filter Bridge"
    app_env: str = "development"
    debug: bool = False
    
    # تنظیمات سرور
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # تنظیمات امنیتی
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # تنظیمات دیتابیس
    database_url: Optional[str] = None
    
    # تنظیمات پروکسی
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    
    # تنظیم مدل برای بارگذاری از فایل .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# ایجاد نمونه‌ای از تنظیمات
@lru_cache()
def get_settings() -> Settings:
    """
    تابعی برای دریافت تنظیمات با استفاده از الگوی Singleton
    """
    return Settings()

# نمونه‌ای از تنظیمات برای استفاده در ماژول‌های دیگر
settings = get_settings()
